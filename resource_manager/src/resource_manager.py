import os
import logging
import time
import resource_manager.src.config as config
import resource_manager.src.constants as constants
from resource_manager.src.cloud_formation import CloudFormationTemplate
from resource_manager.src.s3 import S3
from resource_manager.src.resource_model import ResourceModel
from pynamodb.exceptions import PutError
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from enum import Enum
from cfn_tools import load_yaml


class ResourceManager:
    """
    Resource Manager to deploy/access/destroy resources created using Cloud Formation for SSM automation document tests.
    """

    class ResourceType(Enum):
        DEDICATED = 1,
        ON_DEMAND = 2,
        ASSUME_ROLE = 3

        @staticmethod
        def from_string(resource_type):
         for rt in ResourceManager.ResourceType:
            if rt.name == resource_type:
                return rt
         raise Exception('Resource type for name [{}] is not supported.'.format(resource_type))

    def __init__(self):
        self.ddb_lock_client = None
        self.cf_templates = dict()
        self.cf_resources = dict()

    @staticmethod
    def init_ddb_tables():
        """
        Creates DDB tables to be used by tests.
        """
        logging.info("Creating DDB tables.")
        ResourceModel.create_ddb_table()

    def add_cf_template(self, cfn_template_path, resource_type: ResourceType, **cf_input_params):
        """
        Adds cloud formation templates into dict into resource manager instance with input parameters.
        :param cfn_template_path: CF template file path.
        :param resource_type The resource type (ASSUME_ROLE, DEDICATED, ON_DEMAND).
        :param cf_input_params: CF stack input parameters.
        """
        self.cf_templates[cfn_template_path] = {'input_params': cf_input_params, 'type': resource_type}

    def get_cf_output_params(self):
        """
        Returns cloud formation template output parameters for
        all given templates stored in Resource Manager instance.
        Format in which parameters returned can be used as input
        parameters for SSM document execution. However in this
        case Cloud Formation Template output parameter names should match
        SSM document input parameter names.
        Example can be find in:
        AwsDigitoArtifactsGameday/documents/test/RDS/FailoverAuroraCluster/Tests/step_defs/test_aurora_failover_cluster.py
        :return:
        """
        resources = self.pull_resources()
        parameters = {}
        for resource in resources:
            for out in resource.attribute_values['cf_output_parameters']:
                cf_template_name = self._get_cf_template_file_name(resource.cf_template_name)
                if parameters.get(cf_template_name) is None:
                    parameters[cf_template_name] = {}
                parameters[cf_template_name][out['OutputKey']] = out['OutputValue']
        return parameters

    def pull_resources(self):
        """
        Pulls available resources for all cloud formation templates used by test.
        :return: The available resources.
        """
        resources = []
        for cf_template_path in self.cf_templates:
            if self.cf_resources.get(cf_template_path) is None:
                cf_template_file_name = self._get_cf_template_file_name(cf_template_path)
                resource_type = self.cf_templates[cf_template_path]['type']
                pool_size = self._get_resource_pool_size(cf_template_file_name, resource_type)
                self.cf_resources[cf_template_path] = self.pull_resource_by_template_name(cf_template_path,
                                                                                          pool_size,
                                                                                          resource_type,
                                                                                          constants.wait_time_out_secs)
            resources.append(self.cf_resources[cf_template_path])
        return resources

    def pull_resource_by_template_name(self, cf_template_path, pool_size: int, resource_type: ResourceType, time_out_sec):
        """
        Pulls 'AVAILABLE' resources from Dynamo DB table by cloud formation template name,
        if resource is not available it waits.
        :param cf_template_path: The cloud formation template path
        :param time_out_sec: The amount of seconds to wait for resource before time out
        :param pool_size The pool size for resource (limit of available copies of given cloud formation template)
        :param resource_type The type of the resource.
        :return: The available resources
        """
        # TODO (semiond): Implement logic to replace create/update
        # resource in case if input parameters does not match for given template:
        # https://issues.amazon.com/issues/Digito-1203
        # TODO: Implement logic to handle DEDICATED/ON_DEMAND resource creation/termination:
        # https://issues.amazon.com/issues/Digito-1204
        # TODO: Implement CF template diff detector to update stack if template changed:
        # https://issues.amazon.com/issues/Digito-1205
        logging.info('Pulling resources for [{}] template'.format(cf_template_path))
        waited_time_sec = 0
        while waited_time_sec < time_out_sec:
            resources = ResourceModel.query(cf_template_path)
            for i in range(pool_size):
                resource = self._filter_resource_by_index(resources, i)
                if resource is None:
                    resource = self._create_resource(i, pool_size, cf_template_path, resource_type)
                    if resource is not None:
                        return resource
                # In case if resource type is ASSUME_ROLE resource will be available always since
                # multiple tests can use same role at the same time.
                elif resource.type == ResourceManager.ResourceType.ASSUME_ROLE.name:
                    return resource
                # In case if resource type is ON_DEMAND resource can be taken by other
                # tests so we should check if resource is AVAILABLE before taking it.
                elif resource.type == ResourceManager.ResourceType.ON_DEMAND.name and \
                        resource.status == ResourceModel.Status.AVAILABLE.name:
                    try:
                        resource.leased_times = resource.leased_times + 1
                        resource.status = ResourceModel.Status.LEASED.name
                        resource.leased_on = datetime.now()
                        resource.updated_on = datetime.now()
                        resource.save()
                        return resource
                    except PutError as e:
                        # In case if object already exist, do nothing
                        pass
                    except Exception as e:
                        logging.error(e)
                        raise e
            logging.warning("No template [%s] resource available with pool size [%d], sleeping for [%d] seconds...",
                            cf_template_path,
                            pool_size,
                            constants.sleep_time_secs)
            time.sleep(constants.sleep_time_secs)
            waited_time_sec = waited_time_sec + constants.sleep_time_secs

        err_message = "Resource retrieving operation timed out in [{}] seconds for [{}] template."\
            .format(time_out_sec, cf_template_path)
        logging.error(err_message)
        raise Exception(err_message)

    def _filter_resource_by_index(self, resources, index):
        if resources is not None:
            for resource in resources:
                if resource.cf_stack_index == index:
                    return resource
        return None

    def release_resources(self):
        """
        Releases resources - updates records in Dynamo DB table with status 'AVAILABLE'.
        """
        logging.info("Releasing test resources.")
        for resource in self.cf_resources.values():
            if resource.type != ResourceManager.ResourceType.ASSUME_ROLE.name:
                ResourceModel.update_resource_status(resource, ResourceModel.Status.AVAILABLE)

    @staticmethod
    def fix_stalled_resources():
        """
        Releases stalled resources - in case if test was cancelled or
        failed we want to release resources for next test iteration.
        """
        logging.info("Releasing all stalled resources.")
        for resource in ResourceModel.scan():
            # If resource was not released because of failure or cancellation
            if resource.status == ResourceModel.Status.LEASED.name:
                ResourceModel.update_resource_status(resource, ResourceModel.Status.AVAILABLE)

            # If resource was not fully created because of failure or cancellation
            elif resource.status == ResourceModel.Status.CREATING.name:
                resource.delete()

    @staticmethod
    def destroy_all_resources():
        """
        Destroys all created resources by executed test.
        This should be performed during testing session completion step.
        To make this step quicker we are performing cloud formation stacks deletion in parallel using ThreadPoolExecutor.
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
                t_executor.submit(ResourceManager._delete_cf_stack, resource)

        # Deleting tables
        logging.info("Deleting DDB table [%s].", ResourceModel.Meta.table_name)
        ResourceModel.delete_table()

        # Deleting S3 bucket
        S3.delete_bucket(S3.get_bucket_name())

    @staticmethod
    def _delete_cf_stack(resource):
        """
        Deleting Cloud Formation stack.
        :param resource: The stack resource record.
        """
        logging.info("Destroying [%s] stack.", resource.cf_stack_name)
        CloudFormationTemplate.delete_cf_stack(resource.cf_stack_name)

    def _get_resource_pool_size(self, cf_template_name, resource_type: ResourceType):
        """
        Using config.py finds pool size for given template
        (number of cloud formation stack copies to be created for given cloud formation template).
        :param cf_template_path: The file path to cloud formation template
        :return: The pool size
        """
        pool_size = 1 if resource_type == ResourceManager.ResourceType.ASSUME_ROLE \
            else config.pool_size.get(cf_template_name)
        if pool_size is None:
            default_pool_size = config.pool_size['default']
            logging.warning("Pool size for [%s] template not found, using default: %d",
                            cf_template_name, default_pool_size)
            return default_pool_size
        logging.info("Pool size for [%s] template: %d", cf_template_name, pool_size)
        return pool_size

    def _create_resource(self, index, pool_size, cfn_template_path, resource_type: ResourceType):
        """
        Creates resource for given cloud formation template.
        :param index: The cloud formation template resource index (should not exceed pool_size limit.)
        :param pool_size: The cloud formation pool size.
        :param cfn_template_path: The cloud formation template path
        :return: The created clkoud formation resources
        """
        cf_stack_name = self._get_stack_name(cfn_template_path, index, resource_type)
        try:
            resource = ResourceModel.create(
                cf_stack_index=index,
                cf_template_name=cfn_template_path,
                pool_size=pool_size,
                cf_stack_name=cf_stack_name,
                type=resource_type.name,
                status=ResourceModel.Status.CREATING.name,
                leased_on=datetime.now(),
                created_on=datetime.now(),
                updated_on=datetime.now()
            )

            # Creating cloud formation stack stack
            cf_template = self.cf_templates.get(cfn_template_path)
            cf_input_params = cf_template['input_params']
            logging.info("Creating stack [%s:%s] with input params [%s]", resource_type.name, cf_stack_name, cf_input_params)
            cf_template_s3_url = S3.upload_file(cfn_template_path)
            cf_output_params = CloudFormationTemplate.deploy_cf_stack(cf_template_s3_url,
                                                                      cf_stack_name, **cf_input_params)

            # Updating record and leasing (is not ASSUME_ROLE) for waiting thread
            status = ResourceModel.Status.AVAILABLE.name if \
                resource_type == ResourceManager.ResourceType.ASSUME_ROLE.name \
                else ResourceModel.Status.LEASED.name
            resource.status = status
            resource.cf_template_url = cf_template_s3_url
            resource.leased_times = resource.leased_times + 1
            resource.cf_input_parameters = cf_input_params
            resource.cf_output_parameters = cf_output_params
            resource.save()
            return resource
        except PutError as e:
            return None
        except Exception as e:
            logging.error(e)
            raise e

    def _get_stack_name(self, cf_template_path: str, index: int, resource_type: ResourceType):
        """
        Returns name of the stack to be deployed. For ASSUME_ROLE resource type we take name from cfn template Outputs,
        for other cases cfn stack name will be equal to template file name.
        :param cf_template_path The cloud formation template path
        :param index The stack index to be appended to stack name.
        :param resource_type The resource type (ON_DEMAND, ASSUME_ROLE or DEDICATED)
        """
        if resource_type == ResourceManager.ResourceType.ASSUME_ROLE:
            cf_template_file = None
            try:
                cf_template_file = open(cf_template_path)
                data = load_yaml(cf_template_file)
                if data['Outputs'] is None:
                    raise Exception('Assume role template [{}] requires "Outputs" with role name parameter.'
                                    .format(cf_template_path))
                return data['Outputs'].items()[0][0] + '-' + str(index)
            finally:
                if cf_template_file:
                    cf_template_file.close()
        else:
            return self._get_cf_template_file_name(cf_template_path) + '-' + str(index)

    def _get_cf_template_file_name(self, cfn_template_path: str):
        """
        Returns tuple of cloud formation template file name and extension pair.
        :param cfn_template_path The cloud formation template path
        """
        if not os.path.isfile(cfn_template_path):
            raise FileNotFoundError('Cloud formation template with name [{}] does not exist.'.format(cfn_template_path))
        base_name = os.path.basename(cfn_template_path)
        (file_name, ext) = os.path.splitext(base_name)
        return file_name
