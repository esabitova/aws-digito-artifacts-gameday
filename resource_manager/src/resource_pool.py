import os
import logging
import time
import copy
import re
import resource_manager.src.config as config
import resource_manager.src.constants as constants
import resource_manager.src.util.yaml_util as yaml_util
import resource_manager.src.util.param_utils as param_utils
from .cloud_formation import CloudFormationTemplate
from .s3 import S3
from .resource_model import ResourceModel
from .resource_base import ResourceBase
from pynamodb.exceptions import PutError
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from sttable import parse_str_table


class ResourcePool(ResourceBase):
    """
    Resource Pool to deploy/access/destroy resources created using Cloud Formation for SSM automation document tests.
    """

    CFN_TEMPLATE_NAME_PARAM = 'CfnTemplateName'
    CFN_TEMPLATE_PATH_PARAM = 'CfnTemplatePath'
    CFN_INPUT_PARAMS_PARAM = 'CfnInputParams'
    CFN_OUTPUT_PARAMS_PARAM = 'CfnOutputParams'
    CFN_RESOURCE_TYPE_PARAM = 'ResourceType'
    CFN_RESOURCE_PARAM = 'CfnResource'
    CFN_DEPENDENCY_STACKS_PARAM = 'CfnDependencyStackNames'

    def __init__(self, cfn_helper: CloudFormationTemplate, s3_helper: S3, custom_pool_size: dict, test_session_id: str,
                 ssm_test_cache: {}, logger=logging.getLogger()):
        self.cfn_helper = cfn_helper
        self.s3_helper = s3_helper
        self.cfn_templates = {}
        self.custom_pool_size = custom_pool_size
        self.test_session_id = test_session_id
        self.ssm_test_cache = ssm_test_cache
        self.logger = logger

    def init_ddb_tables(self, boto3_session):
        """
        Creates DDB tables to be used by tests.
        :param boto3_session The AWS boto3 session
        """
        self.logger.info("Creating DDB tables.")
        ResourceModel.configure(boto3_session)
        ResourceModel.create_ddb_table()

    def add_cfn_templates(self, cfn_templates: str):
        """
        Adds cloud formation templates into dict into resource manager instance with input parameters.
        :param cfn_templates: The cfn templates configuration string representation of table:

        |CfnTemplatePath   |ResourceType|TestParamA             |TestParamB                              |
        |TestTemplateA.yml |      SHARED|test_value             |                                        |
        |TestTemplateB.yml |   ON_DEMAND|{{cache:ParamA>ParamB}}|{{cfn-output:TestTemplateA>OutputParam}}|
        |TestTemplateC.yml |   DEDICATED|                       |{{cfn-output:TestTemplateB>OutputParam}}|
        """
        for cfn_template in parse_str_table(cfn_templates).rows:
            if cfn_template.get(ResourcePool.CFN_TEMPLATE_PATH_PARAM) is None or \
                    len(ResourcePool.CFN_TEMPLATE_PATH_PARAM) < 1 \
                    or cfn_template.get(ResourcePool.CFN_RESOURCE_TYPE_PARAM) is None or \
                    len(cfn_template.get(ResourcePool.CFN_RESOURCE_TYPE_PARAM)) < 1:
                err_message = f'Required parameters [{ResourcePool.CFN_TEMPLATE_PATH_PARAM}] '\
                              f'and [{ResourcePool.CFN_RESOURCE_TYPE_PARAM}] should be presented.'
                self.logger.error(err_message)
                raise Exception(err_message)

            res_type = ResourceModel.Type.from_string(cfn_template.pop(ResourcePool.CFN_RESOURCE_TYPE_PARAM))
            cfn_temp_path = cfn_template.pop(ResourcePool.CFN_TEMPLATE_PATH_PARAM)
            cfn_temp_name = self._get_cfn_template_file_name(cfn_temp_path, res_type)

            # For assume roles we are combining template content into a single cfn stack,
            # no collision will happen for same template name, however no duplicated cfn path is allowed.
            if self.cfn_templates.get(cfn_temp_path) or (self._get_cfn_temp_path_by_name(cfn_temp_name) is not None
                                                         and ResourceModel.Type.ASSUME_ROLE != res_type):
                err_message = f'Duplicated cfn template [{cfn_temp_name}] name for path [{cfn_temp_path}].'
                self.logger.error(err_message)
                raise Exception(err_message)

            # Validate parameters
            cfn_in_params = self._parse_cfn_inputs(cfn_template)
            for param, value in cfn_in_params.items():
                if re.compile(r'{{2}(cfn-output:).+}{2}').match(value):
                    dep_cfn_template_name, dep_cfn_output_param = param_utils.parse_cfn_output_val_ref(value)
                    dep_cfn_temp_path = self._get_cfn_temp_path_by_name(dep_cfn_template_name)
                    if not dep_cfn_temp_path:
                        err_message = f'Cloud formation template for name [{dep_cfn_template_name}] ' \
                                      f'was not configured in test.'
                        self.logger.error(err_message)
                        raise Exception(err_message)
                    dep_cfn_template = self.cfn_templates[dep_cfn_temp_path]
                    dep_res_type = dep_cfn_template[ResourcePool.CFN_RESOURCE_TYPE_PARAM]
                    if res_type != ResourceModel.Type.DEDICATED and dep_res_type == ResourceModel.Type.DEDICATED:
                        err_message = f'Resource for template name [{cfn_temp_name}] type [{res_type.name}] ' \
                                      f'cannot depend on resource type [{dep_res_type.name}] ' \
                                      f'with template name [{dep_cfn_template_name}]. Once resource with type ' \
                                      f'[{dep_res_type.name}]  is deleted, child resource will not be able to use it.'
                        raise Exception(err_message)
                    elif dep_res_type == ResourceModel.Type.ASSUME_ROLE:
                        err_message = f'Resource for template name [{cfn_temp_name}] type [{res_type.name}] ' \
                                      f'cannot depend on resource type [{dep_res_type.name}] ' \
                                      f'with template name [{dep_cfn_template_name}]. ' \
                                      f'ASSUME_ROLE should be used only for SSM document execution.'
                        raise Exception(err_message)

            self.cfn_templates[cfn_temp_path] = {ResourcePool.CFN_TEMPLATE_NAME_PARAM: cfn_temp_name,
                                                 ResourcePool.CFN_INPUT_PARAMS_PARAM: cfn_in_params,
                                                 ResourcePool.CFN_RESOURCE_TYPE_PARAM: res_type,
                                                 ResourcePool.CFN_RESOURCE_PARAM: None,
                                                 ResourcePool.CFN_OUTPUT_PARAMS_PARAM: {},
                                                 ResourcePool.CFN_DEPENDENCY_STACKS_PARAM: []}

    def get_cfn_output_params(self):
        """
        Returns cloud formation template output parameters for
        all given templates stored in Resource Manager instance.
        Format in which parameters returned can be used as input
        parameters for SSM document execution. However in this
        case Cloud Formation Template output parameter names should match
        SSM document input parameter names.
        Example can be find in:
        AwsDigitoArtifactsGameday/documents/test/RDS/FailoverAuroraCluster/Tests/step_defs/test_aurora_failover_cluster.py
        :return The cloud formation stack output parameters.
        """
        cfn_output_params = {}
        resources = self.pull_resources()
        for cfn_config in resources.values():
            resource = cfn_config[ResourcePool.CFN_RESOURCE_PARAM]
            cfn_name = cfn_config[ResourcePool.CFN_TEMPLATE_NAME_PARAM]
            cfn_output_params[cfn_name] = self._parse_cfn_outputs(resource)
        return cfn_output_params

    def pull_resources(self) -> []:
        """
        Pulls available resources for all cloud formation templates used by test.
        :return: The available resources.
        """
        for cfn_template in self.cfn_templates.items():
            cfn_config = cfn_template[1]
            if not cfn_config.get(ResourcePool.CFN_RESOURCE_PARAM):
                cfn_config[ResourcePool.CFN_RESOURCE_PARAM] = self.pull_resource_by_template(cfn_template)
        return self.cfn_templates

    def pull_resource_by_template(self, cfn_template: ()):
        """
        Pulls 'AVAILABLE' resources from Dynamo DB table by cloud formation template name,
        if resource is not available it waits.
        :param cfn_template: The cloud formation template object containing cloud formation configuration.
        :return: The available resources
        """
        cfn_template_path = cfn_template[0]
        cfn_config = cfn_template[1]
        cfn_template_name = cfn_config[ResourcePool.CFN_TEMPLATE_NAME_PARAM]
        resource_type = cfn_config[ResourcePool.CFN_RESOURCE_TYPE_PARAM]
        cfn_input_params = self._parse_cfn_input_params(cfn_config)
        pool_size = self._get_resource_pool_size(cfn_template_name, resource_type)
        time_out_sec = constants.wait_time_out_secs
        self.logger.info('Pulling resources for [{}] template'.format(cfn_template_path))

        waited_time_sec = 0
        while waited_time_sec < time_out_sec:
            cfn_template_path_by_type = self._get_cfn_template_path_by_type(cfn_template_path, resource_type)
            resources = ResourceModel.query(cfn_template_path_by_type)
            for i in range(pool_size):
                resource = self._filter_resource_by_index_and_type(resources, i, resource_type)
                try:
                    if resource is None:
                        resource = self._create_resource(i, pool_size, cfn_template_path,
                                                         cfn_input_params, resource_type)
                        if resource is not None:
                            return resource
                    # In case if resource is AVAILABLE/FAILED. In case of FAILED we want to
                    # give a try to update resource so that testing session is not terminated.
                    elif resource.status == ResourceModel.Status.AVAILABLE.name or \
                            resource.status == ResourceModel.Status.FAILED.name or \
                            resource.status == ResourceModel.Status.DELETED.name:
                        cfn_content = yaml_util.file_loads_yaml(cfn_template_path)

                        # In case if resource type is ASSUME_ROLE
                        if resource.type == ResourceModel.Type.ASSUME_ROLE.name:
                            existing_assume_roles = self._get_s3_cfn_content(config.ssm_assume_role_cfn_s3_path)
                            merged_roles = self._merge_assume_roles(existing_assume_roles, cfn_content)
                            if not yaml_util.is_equal(merged_roles, existing_assume_roles) or \
                                    resource.status == ResourceModel.Status.FAILED.name or \
                                    resource.status == ResourceModel.Status.DELETED.name:
                                resource = self._update_resource(i, cfn_template_path, cfn_input_params,
                                                                 merged_roles, resource)
                                if resource is not None:
                                    return resource
                            else:
                                return resource
                        else:
                            cfn_template_sha1 = yaml_util.get_yaml_file_sha1_hash(cfn_template_path)
                            cfn_params_sha1 = yaml_util.get_yaml_content_sha1_hash(cfn_input_params)

                            if resource.cf_template_sha1 != cfn_template_sha1 \
                                    or resource.cf_input_parameters_sha1 != cfn_params_sha1 \
                                    or resource.status == ResourceModel.Status.FAILED.name \
                                    or resource.status == ResourceModel.Status.DELETED.name:
                                resource = self._update_resource(i, cfn_template_path, cfn_input_params,
                                                                 cfn_content, resource)
                                if resource is not None:
                                    return resource
                            # In case if resource type is ON_DEMAND or DEDICATED
                            elif resource.type == ResourceModel.Type.ON_DEMAND.name or \
                                    resource.type == ResourceModel.Type.DEDICATED.name:
                                resource.leased_times = resource.leased_times + 1
                                resource.status = ResourceModel.Status.LEASED.name
                                resource.leased_on = datetime.now()
                                resource.updated_on = datetime.now()
                                resource.test_session_id = self.test_session_id
                                resource.cfn_dependency_stacks = \
                                    self._get_cfn_dependency_stacks(cfn_template_path, resource_type)
                                resource.save()
                                return resource
                            # In case if resource type is SHARED
                            else:
                                return resource
                except PutError:
                    # In case if object already exist, do nothing
                    pass
                except Exception as e:
                    self.logger.error(e)
                    raise e

            self.logger.info(f'Resources for template [{cfn_template_name}:{resource_type.name}] and pool size '
                             f'[{pool_size}] not available, waiting for [{constants.sleep_time_secs}] seconds.')
            time.sleep(constants.sleep_time_secs)
            waited_time_sec = waited_time_sec + constants.sleep_time_secs

        err_message = f'Resource retrieving operation timed out in [{time_out_sec}] ' \
                      f'seconds for [{cfn_template_path}] template.'
        self.logger.error(err_message)
        raise Exception(err_message)

    def _filter_resource_by_index_and_type(self, resources: [], index: int,
                                           resource_type: ResourceModel.Type) -> ResourceModel:
        """
        Filters list of resources by given index.
        :param resources The list of given resources to filter
        :param index The index of resource
        """
        if resources is not None:
            for resource in resources:
                if resource.cf_stack_index == index and resource.type == resource_type.name:
                    return resource
        return None

    def release_resources(self):
        """
        Releases resources - updates records in Dynamo DB table with status 'AVAILABLE'.
        """
        self.logger.info("Releasing test resources.")
        # We do release/delete resources in reverse order, from bottom to top
        # due to possible relations between resources.
        for cfn_config in reversed(list(self.cfn_templates.values())):
            resource = cfn_config[ResourcePool.CFN_RESOURCE_PARAM]
            if resource:
                if resource.type == ResourceModel.Type.DEDICATED.name:
                    # Deleting resource/stack for DEDICATED type.
                    cfn_stack_name = resource.cf_stack_name
                    try:
                        ResourceModel.update_resource_status(resource, ResourceModel.Status.DELETING)
                        # Delete stack.
                        self.cfn_helper.delete_cf_stack(cfn_stack_name)
                        ResourceModel.update_resource_status(resource, ResourceModel.Status.DELETED)
                    except Exception as e:
                        self.logger.error(f'Failed to delete [{cfn_stack_name}] stack due to: {e}')
                        ResourceModel.update_resource_status(resource, ResourceModel.Status.DELETE_FAILED)
                elif resource.status == ResourceModel.Status.LEASED.name:
                    ResourceModel.update_resource_status(resource, ResourceModel.Status.AVAILABLE)

    def fix_stalled_resources(self):
        """
        Releases stalled resources - in case if test was cancelled or
        failed we want to release resources for next test iteration.
        """
        self.logger.info("Releasing all stalled resources.")
        for resource in ResourceModel().scan():
            if not self.test_session_id or resource.test_session_id == self.test_session_id:
                # If resource was not released because of failure or cancellation
                if resource.status == ResourceModel.Status.LEASED.name:
                    ResourceModel.update_resource_status(resource, ResourceModel.Status.AVAILABLE)
                # If resource was not fully created/updated because of failure or cancellation
                elif resource.status != ResourceModel.Status.AVAILABLE.name and \
                        resource.status != ResourceModel.Status.FAILED.name and \
                        resource.status != ResourceModel.Status.DELETED.name:
                    self.logger.info(f'Deleting resource for stack name [{resource.cf_stack_name}] '
                                     f'in status [{resource.status}].')
                    resource.delete()

    def destroy_all_resources(self):
        """
        Destroys all created resources by executed test.
        This should be performed during testing session completion step.
        To make this step quicker we are performing cloud formation stacks deletion in
        parallel using ThreadPoolExecutor.
        """
        # Deleting stacks
        resources = []
        for resource in ResourceModel.scan():
            resources.append(resource)
        resource_count = len(resources)
        self.logger.info("Deleting [%d] cloud formation stacks.", resource_count)
        with ThreadPoolExecutor(max_workers=10) as t_executor:
            for index in range(resource_count):
                resource_to_delete = resources[index]
                t_executor.submit(ResourcePool._delete_resource, resource_to_delete,
                                  self.cfn_helper, self.logger, resources)

        # Deleting DDB table
        failed_resources = []
        for resource in ResourceModel.scan():
            if resource.status == ResourceModel.Status.DELETE_FAILED.name:
                self.logger.error(f'Deleting [{resource.cf_stack_name}] stack failed.')
                failed_resources.append(resource)
            else:
                resource.delete()

        bucket_name = self.s3_helper.get_bucket_name()
        if len(failed_resources) > 0:
            err_message = f'Failed to delete [{ResourceModel.Meta.table_name}] DDB table and [{bucket_name}] ' \
                          f'S3 bucket due CFN stack deletion failure. For investigation purpose we do not ' \
                          f'delete DDB table and S3 bucket ' \
                          f'(feel free to delete DDB table/S3 bucket manually when ready). '
            self.logger.error(err_message)
            raise Exception(err_message)
        else:
            self.logger.info("Deleting DDB table [%s].", ResourceModel.Meta.table_name)
            ResourceModel.delete_table()

            # Deleting S3 bucket
            self.s3_helper.delete_bucket(bucket_name)

    def _get_resource_pool_size(self, cfn_template_name: str, resource_type: ResourceModel.Type) -> int:
        """
        Finds pool size (number of cloud formation stack copies to be created for given cloud formation template)
        defined in config.pool_size or custom_pool_size for given template
        if custom_pool_size has configuration for cfn_template_name it will override config.pool_size.
        :param cfn_template_name The file path to cloud formation template
        :return The pool size
        """
        pool_size = 1
        if resource_type != ResourceModel.Type.ON_DEMAND and \
                resource_type != ResourceModel.Type.DEDICATED:
            return pool_size
        elif self.custom_pool_size and self.custom_pool_size.get(cfn_template_name)\
                and self.custom_pool_size.get(cfn_template_name).get(resource_type):
            pool_size = self.custom_pool_size.get(cfn_template_name).get(resource_type)
        else:
            pool_size_config = config.pool_size.get(cfn_template_name)
            if pool_size_config is None or pool_size_config.get(resource_type) is None:
                self.logger.warning("Pool size for [%s:%s] template not found, using default: %d",
                                    cfn_template_name, resource_type.name, pool_size)
                pool_size = config.pool_size['default']

            else:
                pool_size = pool_size_config.get(resource_type)
        self.logger.info("Pool size for [%s:%s] template: %d", cfn_template_name, resource_type.name, pool_size)
        return pool_size

    def _update_resource(self, index: int, cfn_template_path: str, cfn_input_params: {},
                         cfn_content: dict, resource: ResourceModel):
        """
        Updates resource for given cloud formation template.
        :param index: The cloud formation template resource index (should not exceed pool_size limit.)
        :param cfn_template_path: The cloud formation template path
        :param cfn_input_params: The cloud formation input parameters
        :param cfn_content: The cloud formation content
        :param resource: The resource to be updated
        :return The updated cloud formation resource
        """
        try:
            cfn_content_sha1 = yaml_util.get_yaml_content_sha1_hash(cfn_content)
            resource_type = ResourceModel.Type.from_string(resource.type)
            cfn_input_params_sha1 = yaml_util.get_yaml_content_sha1_hash(cfn_input_params)
            cfn_template_path_by_type = self._get_cfn_template_path_by_type(cfn_template_path, resource_type)
            cfn_stack_name = self._get_stack_name(cfn_template_path_by_type, index, resource_type)

            # Changing status to UPDATING/CREATING to block other threads to use it.
            if resource.status == ResourceModel.Status.DELETED.name:
                resource.status = ResourceModel.Status.CREATING.name
            else:
                resource.status = ResourceModel.Status.UPDATING.name
            resource.test_session_id = self.test_session_id
            resource.save()

            # Updating cloud formation stack stack
            self.logger.info("Updating stack [%s:%s] input params: [%s]", resource_type.name, cfn_stack_name,
                             cfn_input_params)
            return self._update_resource_stack(resource, resource_type, cfn_content, cfn_content_sha1,
                                               cfn_template_path_by_type, cfn_stack_name, cfn_input_params_sha1,
                                               cfn_input_params)
        except PutError:
            return None
        except Exception as e:
            # In case if update resource operation failed we mark record status as FAILED
            if resource:
                resource.status = ResourceModel.Status.FAILED.name
                resource.save()
            raise e

    def _create_resource(self, index: int, pool_size: int, cfn_template_path: str, cfn_input_params: {},
                         resource_type: ResourceModel.Type):
        """
        Creates resource for given cloud formation template.
        :param index The cloud formation template resource index (should not exceed pool_size limit.)
        :param pool_size The cloud formation pool size.
        :param cfn_template_path The cloud formation template path
        :param cfn_input_params: The cloud formation input parameters
        :param resource_type The resource type
        :return The created cloud formation resources
        """
        resource = None
        try:
            cfn_content = yaml_util.file_loads_yaml(cfn_template_path)
            cfn_content_sha1 = yaml_util.get_yaml_content_sha1_hash(cfn_content)
            cfn_input_params_sha1 = yaml_util.get_yaml_content_sha1_hash(cfn_input_params)
            cfn_template_path_by_type = self._get_cfn_template_path_by_type(cfn_template_path, resource_type)
            cfn_stack_name = self._get_stack_name(cfn_template_path_by_type, index, resource_type)

            resource = ResourceModel.create(
                cf_stack_index=index,
                cf_template_name=cfn_template_path_by_type,
                pool_size=pool_size,
                cf_stack_name=cfn_stack_name,
                type=resource_type.name,
                status=ResourceModel.Status.CREATING.name,
                test_session_id=self.test_session_id,
                leased_on=datetime.now(),
                created_on=datetime.now(),
                updated_on=datetime.now()
            )

            # Creating cloud formation stack stack
            self.logger.info("Creating stack [%s:%s] with input params [%s]", resource_type.name, cfn_stack_name,
                             cfn_input_params)
            return self._update_resource_stack(resource, resource_type, cfn_content, cfn_content_sha1,
                                               cfn_template_path, cfn_stack_name, cfn_input_params_sha1,
                                               cfn_input_params)
        except PutError:
            return None
        except Exception as e:
            # In case if create resource operation failed we mark record status as FAILED
            if resource:
                resource.status = ResourceModel.Status.FAILED.name
                resource.save()
            raise e

    def _update_resource_stack(self, resource: ResourceModel, resource_type: ResourceModel.Type,
                               cfn_content: dict, cfn_content_sha1: str, cfn_template_path: str, cfn_stack_name: str,
                               cfn_input_params_sha1: str, cfn_input_params):
        """
        Updating resource stack and state based on given parameters.
        :param resource The resource record model from DDB
        :param resource_type The resource type
        :param cfn_content The content of cloud formation template
        :param cfn_template_path The cloud formation template path to be stored in DDB.
        :param cfn_stack_name The cloud formation stack name
        :param cfn_input_params The cloud formation input parameters
        """

        cfn_template_s3_url = self.s3_helper.upload_file(cfn_template_path, cfn_content)
        cf_output_params = self.cfn_helper.deploy_cf_stack(cfn_template_s3_url,
                                                           cfn_stack_name,
                                                           **cfn_input_params)

        resource.cf_template_url = cfn_template_s3_url
        resource.leased_times = resource.leased_times + 1
        resource.cf_input_parameters = cfn_input_params
        resource.cf_input_parameters_sha1 = cfn_input_params_sha1
        resource.cf_output_parameters = cf_output_params
        resource.test_session_id = self.test_session_id
        resource.cf_template_sha1 = cfn_content_sha1
        resource.cfn_dependency_stacks = self._get_cfn_dependency_stacks(cfn_template_path, resource_type)
        if resource_type == ResourceModel.Type.ON_DEMAND or \
                resource_type == ResourceModel.Type.DEDICATED:
            resource.status = ResourceModel.Status.LEASED.name
        else:
            resource.status = ResourceModel.Status.AVAILABLE.name
        resource.save()
        return resource

    def _parse_cfn_input_params(self, cfn_config: {}) -> {}:
        """
        Parsing cfn input parameters, if cfn input parameter value is pointing to
        '{{cfn-output:TemplateName>TemplateOutput}}' parameter, value is parsed from cfn template output, if referring
        to '{{cache:CachedParamNameA>CachedParamNameB}}' parsed from cache, otherwise value is taken as is.
        :param cfn_config: The cloud formation input parameters.
        :return: The parsed cfn input parameters.
        """
        # Parsing cfn input parameters, if any of parameters is cfn-output,
        # then we pull that cfn resource to get parameter value from cfn output.
        cfn_input_params = cfn_config[ResourcePool.CFN_INPUT_PARAMS_PARAM]
        for param, value in cfn_input_params.items():
            # In case if parameter value refers to cfn output.
            if re.compile(r'{{2}(cfn-output:).+}{2}').match(value):
                cfn_template_name, cfn_output_param = param_utils.parse_cfn_output_val_ref(value)
                cfn_template_path = self._get_cfn_temp_path_by_name(cfn_template_name)
                cfn_template_config = self.cfn_templates.get(cfn_template_path)
                if not cfn_template_config or not cfn_template_config.get(ResourcePool.CFN_RESOURCE_PARAM):
                    cfn_template = (cfn_template_path, cfn_template_config)
                    cfn_template_config[ResourcePool.CFN_RESOURCE_PARAM] = self.pull_resource_by_template(cfn_template)
                resource = cfn_template_config.get(ResourcePool.CFN_RESOURCE_PARAM)
                cfn_input_params[param] = self._parse_cfn_outputs(resource)[cfn_output_param]
                cfn_config[ResourcePool.CFN_DEPENDENCY_STACKS_PARAM].append(resource.cf_stack_name)
            # In case if parameter value refers to cache or is regular value.
            else:
                cfn_input_params[param] = param_utils.parse_param_value(value, {'cache': self.ssm_test_cache})
        return cfn_input_params

    def _get_cfn_template_path_by_type(self, cfn_template_path: str, resource_type: ResourceModel.Type):
        """
        Returns template name used in DDB based on resource type.
        For ASSUME_ROLE type we use static path defined 'config.ssm_assume_role_cfn_s3_path'.
        :param cfn_template_path The cloud formation template file path
        :param resource_type The resource type
        :return The template name used in DDB based on resource type.
        """
        return config.ssm_assume_role_cfn_s3_path if \
            resource_type == ResourceModel.Type.ASSUME_ROLE else cfn_template_path

    def _get_s3_cfn_content(self, cfn_template_path: str):
        """
        Returns file content from S3.
        :param cfn_template_path The cloud formation template file path in S3
        :return The cloud formation file content from S3
        """
        bucket_name = self.s3_helper.get_bucket_name()
        existing_assume_roles_content = self.s3_helper.get_file_content(bucket_name, cfn_template_path)
        if existing_assume_roles_content is None:
            return yaml_util.loads_yaml('{"AWSTemplateFormatVersion": "2010-09-09",'
                                        '"Description": "Assume Roles for SSM automation execution.",'
                                        '"Outputs": {},'
                                        '"Resources": {}}')
        return yaml_util.loads_yaml(existing_assume_roles_content)

    def _merge_assume_roles(self, base_assume_role_cfn_json, add_assume_role_cfn_json):
        """
        Merging/replacing base (existing) assume role content with role which is not yet in existing content.
        :param base_assume_role_cfn_json The existing assume role content
        :param add_assume_role_cfn_json The role content to be merged to existing
        :return The merged cloud formation template content for assume roles.
        """
        cfn_base_copy = copy.deepcopy(base_assume_role_cfn_json)
        for key, val in add_assume_role_cfn_json['Outputs'].items():
            cfn_base_copy['Outputs'][key] = val
        for key, val in add_assume_role_cfn_json['Resources'].items():
            cfn_base_copy['Resources'][key] = val
        return cfn_base_copy

    def _get_stack_name(self, cfn_template_path: str, index: int, resource_type: ResourceModel.Type):
        """
        Returns name of the stack to be deployed. For ASSUME_ROLE resource type we take name from cfn template Outputs,
        for other cases cfn stack name will be equal to template file name.
        :param cfn_template_path The cloud formation template path
        :param index The stack index to be appended to stack name.
        :param resource_type The resource type (ON_DEMAND, ASSUME_ROLE or DEDICATED)
        :return The stack name.
        """
        return f'{self._get_cfn_template_file_name(cfn_template_path, resource_type)}' \
               f'-{resource_type.name.replace("_","-")}-{str(index)}'

    def _get_cfn_template_file_name(self, cfn_template_path: str, resource_type: ResourceModel.Type):
        """
        Returns tuple of cloud formation template file name and extension pair.
        :param cfn_template_path The cloud formation template path
        :return The cloud formation file name with no extension.
        """
        if resource_type != ResourceModel.Type.ASSUME_ROLE and not os.path.isfile(cfn_template_path):
            raise FileNotFoundError('Cloud formation template with name [{}] does not exist.'.format(cfn_template_path))
        base_name = os.path.basename(cfn_template_path)
        (file_name, ext) = os.path.splitext(base_name)
        return file_name

    def _parse_cfn_outputs(self, resource: ResourceModel) -> {}:
        """
        Returns cloud formation outputs as dictionary.
        :param resource: The resource to read cloud formation outputs
        :return: The cloud formation outputs as dictionary.
        """
        cfn_output_parameters = resource.attribute_values.get('cf_output_parameters')
        parsed_cfn_output_parameters = {}
        if cfn_output_parameters is not None:
            for out in cfn_output_parameters:
                parsed_cfn_output_parameters[out['OutputKey']] = out['OutputValue']
        return parsed_cfn_output_parameters

    def _parse_cfn_inputs(self, cfn_template) -> {}:
        """
        Returns cloud formation input parameters in cloud formation acceptable format.
        :param cfn_template: The cloud formation template object with configuration
        :return: The cloud formation input parameters in cloud formation acceptable format
        """
        cfn_input_params = {}
        for param, value in cfn_template.items():
            if len(value) > 0:
                cfn_input_params[param] = str(value)
        return cfn_input_params

    def _get_cfn_temp_path_by_name(self, cfn_template_name: str) -> str:
        """
        Returns cfn template path by given cfn template name:
           - path: path/to/my/my_test_template.yml
           - name: my_test_template
        :param cfn_template_name: The given cfn template name
        :return: The cfn template path
        """
        for cfn_path, cfn_config in self.cfn_templates.items():
            if cfn_template_name == cfn_config.get(ResourcePool.CFN_TEMPLATE_NAME_PARAM):
                return cfn_path
        return None

    def _get_cfn_dependency_stacks(self, cfn_template_path: str, resource_type: ResourceModel.Type) -> []:
        """
        Returns list of cfn dependent stacks.
        :param cfn_template_path: The cfn template path
        :param resource_type: The cfn resource type (ON_DEMAND | DEDICATED | ASSUME_ROLE | SHARED )
        :return: The list of cfn dependent stacks.
        """
        if resource_type != ResourceModel.Type.ASSUME_ROLE:
            return self.cfn_templates[cfn_template_path][ResourcePool.CFN_DEPENDENCY_STACKS_PARAM]
        return []
