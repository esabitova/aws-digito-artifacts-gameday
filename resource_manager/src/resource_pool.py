import os
import logging
import time
import copy
import resource_manager.src.config as config
import resource_manager.src.constants as constants
import resource_manager.src.util.yaml_util as yaml_util
from .cloud_formation import CloudFormationTemplate
from .s3 import S3
from .resource_model import ResourceModel
from pynamodb.exceptions import PutError
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from enum import Enum


class ResourcePool:
    """
    Resource Pool to deploy/access/destroy resources created using Cloud Formation for SSM automation document tests.
    """

    class ResourceType(Enum):
        DEDICATED = 1,
        ON_DEMAND = 2,
        ASSUME_ROLE = 3,
        SHARED = 4

        @staticmethod
        def from_string(resource_type):
            for rt in ResourcePool.ResourceType:
                if rt.name == resource_type:
                    return rt
            raise Exception('Resource type for name [{}] is not supported.'.format(resource_type))

    def __init__(self, cfn_helper: CloudFormationTemplate, s3_helper: S3, custom_pool_size: dict, test_session_id: str):
        self.cfn_helper = cfn_helper
        self.s3_helper = s3_helper
        self.cfn_templates = dict()
        self.cfn_resources = dict()
        self.custom_pool_size = custom_pool_size
        self.test_session_id = test_session_id

    def init_ddb_tables(self, boto3_session):
        """
        Creates DDB tables to be used by tests.
        :param boto3_session The AWS boto3 session
        """
        logging.info("Creating DDB tables.")
        ResourceModel.configure(boto3_session)
        ResourceModel.create_ddb_table()

    def add_cfn_template(self, cfn_template_path, resource_type: ResourceType, **cf_input_params):
        """
        Adds cloud formation templates into dict into resource manager instance with input parameters.
        :param cfn_template_path: CF template file path.
        :param resource_type The resource type (ASSUME_ROLE, DEDICATED, ON_DEMAND).
        :param cf_input_params CF stack input parameters.
        """
        if self.cfn_templates.get(cfn_template_path):
            raise Exception(f'Duplicated cfn template for path [{cfn_template_path}].')
        self.cfn_templates[cfn_template_path] = {'input_params': cf_input_params, 'type': resource_type}

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
        resources = self.pull_resources()
        parameters = {}
        for resource in resources:
            resource_type = ResourcePool.ResourceType.from_string(resource.type)
            template_file_name = self._get_cfn_template_file_name(resource.cf_template_name, resource_type)
            cfn_output_parameters = resource.attribute_values.get('cf_output_parameters')
            if cfn_output_parameters is not None:
                for out in cfn_output_parameters:
                    if parameters.get(template_file_name) is None:
                        parameters[template_file_name] = {}
                    parameters[template_file_name][out['OutputKey']] = out['OutputValue']
        return parameters

    def pull_resources(self):
        """
        Pulls available resources for all cloud formation templates used by test.
        :return: The available resources.
        """
        resources = []
        for cfn_template_path in self.cfn_templates:
            resource_type = self.cfn_templates[cfn_template_path]['type']
            if self.cfn_resources.get(cfn_template_path) is None:
                cf_template_file_name = self._get_cfn_template_file_name(cfn_template_path, resource_type)
                pool_size = self._get_resource_pool_size(cf_template_file_name, resource_type)
                self.cfn_resources[cfn_template_path] = self.pull_resource_by_template(cfn_template_path,
                                                                                       pool_size,
                                                                                       resource_type,
                                                                                       constants.wait_time_out_secs)
            resources.append(self.cfn_resources[cfn_template_path])
        return resources

    def pull_resource_by_template(self, cfn_template_path: str, pool_size: int,
                                  resource_type: ResourceType, time_out_sec: int):
        """
        Pulls 'AVAILABLE' resources from Dynamo DB table by cloud formation template name,
        if resource is not available it waits.
        :param cfn_template_path: The cloud formation template path
        :param time_out_sec: The amount of seconds to wait for resource before time out
        :param pool_size The pool size for resource (limit of available copies of given cloud formation template)
        :param resource_type The type of the resource.
        :return: The available resources
        """
        # TODO: Implement logic to handle DEDICATED resource creation/termination:
        # https://issues.amazon.com/issues/Digito-1204
        logging.info('Pulling resources for [{}] template'.format(cfn_template_path))
        waited_time_sec = 0
        while waited_time_sec < time_out_sec:
            cfn_template_name = self._get_cfn_template_name_by_type(cfn_template_path, resource_type)
            resources = ResourceModel.query(cfn_template_name)
            for i in range(pool_size):
                resource = self._filter_resource_by_index_and_type(resources, i, resource_type)
                try:
                    if resource is None:
                        resource = self._create_resource(i, pool_size, cfn_template_path, resource_type)
                        if resource is not None:
                            return resource
                    # In case if resource is AVAILABLE/FAILED. In case of FAILED we want to
                    # give a try to update resource so that testing session is not terminated.
                    elif resource.status == ResourceModel.Status.AVAILABLE.name or \
                            resource.status == ResourceModel.Status.FAILED.name:
                        cfn_content = yaml_util.file_loads_yaml(cfn_template_path)

                        # In case if resource type is ASSUME_ROLE
                        if resource.type == ResourcePool.ResourceType.ASSUME_ROLE.name:
                            existing_assume_roles = self._get_s3_cfn_content(config.ssm_assume_role_cfn_s3_path)
                            merged_roles = self._merge_assume_roles(existing_assume_roles, cfn_content)
                            if not yaml_util.is_equal(merged_roles, existing_assume_roles) or \
                                    resource.status == ResourceModel.Status.FAILED.name:
                                resource = self._update_resource(i, cfn_template_path, merged_roles, resource)
                                if resource is not None:
                                    return resource
                            else:
                                return resource
                        else:
                            cfn_template_sha1 = yaml_util.get_yaml_file_sha1_hash(cfn_template_path)
                            cfn_params = self._get_cfn_input_parameters(cfn_template_path)
                            cfn_params_sha1 = yaml_util.get_yaml_content_sha1_hash(cfn_params)

                            if resource.cf_template_sha1 != cfn_template_sha1 \
                                    or resource.cf_input_parameters_sha1 != cfn_params_sha1 \
                                    or resource.status == ResourceModel.Status.FAILED.name:
                                resource = self._update_resource(i, cfn_template_path, cfn_content, resource)
                                if resource is not None:
                                    return resource
                            # In case if resource type is ON_DEMAND
                            elif resource.type == ResourcePool.ResourceType.ON_DEMAND.name:
                                resource.leased_times = resource.leased_times + 1
                                resource.status = ResourceModel.Status.LEASED.name
                                resource.leased_on = datetime.now()
                                resource.updated_on = datetime.now()
                                resource.test_session_id = self.test_session_id
                                resource.save()
                                return resource
                            # In case if resource type is SHARED
                            else:
                                return resource
                except PutError:
                    # In case if object already exist, do nothing
                    pass
                except Exception as e:
                    logging.error(e)
                    raise e

            logging.info("No template [%s] resource available with pool size [%d], sleeping for [%d] seconds...",
                         cfn_template_path,
                         pool_size,
                         constants.sleep_time_secs)
            time.sleep(constants.sleep_time_secs)
            waited_time_sec = waited_time_sec + constants.sleep_time_secs

        err_message = "Resource retrieving operation timed out in [{}] seconds for [{}] template."\
            .format(time_out_sec, cfn_template_path)
        logging.error(err_message)
        raise Exception(err_message)

    def _filter_resource_by_index_and_type(self, resources: [], index: int,
                                           resource_type: ResourceType) -> ResourceModel:
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
        logging.info("Releasing test resources.")
        for resource in self.cfn_resources.values():
            if resource.type != ResourcePool.ResourceType.ASSUME_ROLE.name:
                ResourceModel.update_resource_status(resource, ResourceModel.Status.AVAILABLE)

    def fix_stalled_resources(self):
        """
        Releases stalled resources - in case if test was cancelled or
        failed we want to release resources for next test iteration.
        """
        logging.info("Releasing all stalled resources.")
        for resource in ResourceModel().scan():
            if not self.test_session_id or resource.test_session_id == self.test_session_id:
                # If resource was not released because of failure or cancellation
                if resource.status == ResourceModel.Status.LEASED.name:
                    ResourceModel.update_resource_status(resource, ResourceModel.Status.AVAILABLE)
                # If resource was not fully created/updated because of failure or cancellation
                elif resource.status != ResourceModel.Status.AVAILABLE.name and \
                        resource.status != ResourceModel.Status.FAILED.name:
                    logging.info('Deleting resource for stack name [{}] in status [{}].'.format(resource.cf_stack_name,
                                                                                                resource.status))
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
        logging.info("Destroying [%d] cloud formation stacks.", resource_count)
        with ThreadPoolExecutor(max_workers=10) as t_executor:
            for index in range(resource_count):
                resource = resources[index]
                t_executor.submit(ResourcePool._delete_cf_stack, resource, self.cfn_helper)

        # Deleting tables
        logging.info("Deleting DDB table [%s].", ResourceModel.Meta.table_name)
        ResourceModel.delete_table()

        # Deleting S3 bucket
        bucket_name = self.s3_helper.get_bucket_name()
        self.s3_helper.delete_bucket(bucket_name)

    @staticmethod
    def _delete_cf_stack(resource, cfn_helper):
        """
        Deleting Cloud Formation stack.
        :param resource: The stack resource record.
        """
        logging.info("Destroying [%s] stack.", resource.cf_stack_name)
        cfn_helper.delete_cf_stack(resource.cf_stack_name)

    def _get_resource_pool_size(self, cfn_template_name: str, resource_type: ResourceType) -> int:
        """
        Finds pool size (number of cloud formation stack copies to be created for given cloud formation template)
        defined in config.pool_size or custom_pool_size for given template
        if custom_pool_size has configuration for cfn_template_name it will override config.pool_size.
        :param cfn_template_name The file path to cloud formation template
        :return The pool size
        """
        pool_size = 1
        if resource_type != ResourcePool.ResourceType.ON_DEMAND:
            return pool_size
        elif self.custom_pool_size and self.custom_pool_size.get(cfn_template_name):
            pool_size = self.custom_pool_size.get(cfn_template_name)
        else:
            pool_size = config.pool_size.get(cfn_template_name)
            if pool_size is None:
                pool_size = config.pool_size['default']
                logging.warning("Pool size for [%s] template not found, using default: %d",
                                cfn_template_name, pool_size)
        logging.info("Pool size for [%s] template: %d", cfn_template_name, pool_size)
        return pool_size

    def _update_resource(self, index: int, cfn_template_path: str, cfn_content: dict, resource: ResourceModel):
        """
        Updates resource for given cloud formation template.
        :param index: The cloud formation template resource index (should not exceed pool_size limit.)
        :param cfn_template_path: The cloud formation template path
        :param cfn_content: The cloud formation content
        :parma resource: The resource to be updated
        :return The updated cloud formation resource
        """
        try:
            cfn_content_sha1 = yaml_util.get_yaml_content_sha1_hash(cfn_content)
            resource_type = ResourcePool.ResourceType.from_string(resource.type)
            cfn_input_params = self._get_cfn_input_parameters(cfn_template_path)
            cfn_input_params_sha1 = yaml_util.get_yaml_content_sha1_hash(cfn_input_params)
            cfn_template_name = self._get_cfn_template_name_by_type(cfn_template_path, resource_type)
            cfn_stack_name = self._get_stack_name(cfn_template_name, index, resource_type)

            # Changing status to UPDATING to block other threads to use it.
            resource.status = ResourceModel.Status.UPDATING.name
            resource.test_session_id = self.test_session_id
            resource.save()

            # Updating cloud formation stack stack
            logging.info("Updating stack [%s:%s] input params: [%s]", resource_type.name, cfn_stack_name,
                         cfn_input_params)
            return self._update_resource_stack(resource, resource_type, cfn_content, cfn_content_sha1,
                                               cfn_template_name, cfn_stack_name, cfn_input_params_sha1,
                                               cfn_input_params)
        except PutError:
            return None
        except Exception as e:
            # In case if update resource operation failed we mark record status as FAILED
            if resource:
                resource.status = ResourceModel.Status.FAILED.name
                resource.save()
            raise e

    def _create_resource(self, index: int, pool_size: int, cfn_template_path: str, resource_type: ResourceType):
        """
        Creates resource for given cloud formation template.
        :param index The cloud formation template resource index (should not exceed pool_size limit.)
        :param pool_size The cloud formation pool size.
        :param cfn_template_path The cloud formation template path
        :parma resource_type The resource type
        :return The created cloud formation resources
        """
        resource = None
        try:
            cfn_content = yaml_util.file_loads_yaml(cfn_template_path)
            cfn_content_sha1 = yaml_util.get_yaml_content_sha1_hash(cfn_content)
            cfn_input_params = self._get_cfn_input_parameters(cfn_template_path)
            cfn_input_params_sha1 = yaml_util.get_yaml_content_sha1_hash(cfn_input_params)
            cfn_template_name = self._get_cfn_template_name_by_type(cfn_template_path, resource_type)
            cfn_stack_name = self._get_stack_name(cfn_template_name, index, resource_type)

            resource = ResourceModel.create(
                cf_stack_index=index,
                cf_template_name=cfn_template_name,
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
            logging.info("Creating stack [%s:%s] with input params [%s]", resource_type.name, cfn_stack_name,
                         cfn_input_params)
            return self._update_resource_stack(resource, resource_type, cfn_content, cfn_content_sha1,
                                               cfn_template_name, cfn_stack_name, cfn_input_params_sha1,
                                               cfn_input_params)
        except PutError:
            return None
        except Exception as e:
            # In case if create resource operation failed we mark record status as FAILED
            if resource:
                resource.status = ResourceModel.Status.FAILED.name
                resource.save()
            raise e

    def _update_resource_stack(self, resource: ResourceModel, resource_type: ResourceType, cfn_content: dict,
                               cfn_content_sha1: str, cfn_template_name: str, cfn_stack_name: str,
                               cfn_input_params_sha1: str, cfn_input_params):
        """
        Updating resource stack and state based on given parameters.
        :param resource The resource record model from DDB
        :param resource_type The resource type
        :param cfn_content The content of cloud formation template
        :param cfn_template_name The cloud formation template name to be stored in DDB.
        :param cfn_stack_name The cloud formation stack name
        :param cfn_input_params The cloud formation input parameters
        """

        cfn_template_s3_url = self.s3_helper.upload_file(cfn_template_name, cfn_content)
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
        if resource_type == ResourcePool.ResourceType.ON_DEMAND:
            resource.status = ResourceModel.Status.LEASED.name
        else:
            resource.status = ResourceModel.Status.AVAILABLE.name
        resource.save()
        return resource

    def _get_cfn_template_name_by_type(self, cfn_template_path: str, resource_type: ResourceType):
        """
        Returns template name used in DDB based on resource type.
        For ASSUME_ROLE type we use static path defined 'config.ssm_assume_role_cfn_s3_path'.
        :param cfn_template_path The cloud formation template file path
        :param resource_type The resource type
        :return The template name used in DDB based on resource type.
        """
        return config.ssm_assume_role_cfn_s3_path if \
            resource_type == ResourcePool.ResourceType.ASSUME_ROLE else cfn_template_path

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

    def _get_stack_name(self, cfn_template_path: str, index: int, resource_type: ResourceType):
        """
        Returns name of the stack to be deployed. For ASSUME_ROLE resource type we take name from cfn template Outputs,
        for other cases cfn stack name will be equal to template file name.
        :param cfn_template_path The cloud formation template path
        :param index The stack index to be appended to stack name.
        :param resource_type The resource type (ON_DEMAND, ASSUME_ROLE or DEDICATED)
        :return The stack name.
        """
        return self._get_cfn_template_file_name(cfn_template_path, resource_type) + '-' + str(index)

    def _get_cfn_template_file_name(self, cfn_template_path: str, resource_type: ResourceType):
        """
        Returns tuple of cloud formation template file name and extension pair.
        :param cfn_template_path The cloud formation template path
        :return The cloud formation file name with no extension.
        """
        if resource_type != ResourcePool.ResourceType.ASSUME_ROLE and not os.path.isfile(cfn_template_path):
            raise FileNotFoundError('Cloud formation template with name [{}] does not exist.'.format(cfn_template_path))
        base_name = os.path.basename(cfn_template_path)
        (file_name, ext) = os.path.splitext(base_name)
        return file_name

    def _get_cfn_input_parameters(self, cfn_template_path):
        """
        Returns cfn input parameters.
        :param cfn_template_path: The cloud formation template path
        :return: The cfn input parameters.
        """
        cfn_template = self.cfn_templates.get(cfn_template_path)
        return cfn_template['input_params']
