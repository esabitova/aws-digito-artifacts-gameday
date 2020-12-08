import os
import logging
import time
import resource_manager.src.config as config
from resource_manager.src.cloud_formation import CloudFormationTemplate
from resource_manager.src.s3 import S3
from resource_manager.src.resource_model import ResourceModel
from pynamodb.exceptions import PutError
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from enum import Enum
import resource_manager.src.constants as constants


class ResourceManager:
    """
    Resource Manager to deploy/access/destroy resources created using Cloud Formation for SSM automation document tests.
    """

    class ResourceType(Enum):
        DEDICATED = 1,
        ON_DEMAND = 2

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

    def add_cf_template(self, cf_template_name, **cf_input_params):
        """
        Adds cloud formation templates into dict into resource manager instance with input parameters.
        :param cf_template_name: CF template file name.
        :param cf_input_params: CF stack input parameters
        """
        self.cf_templates[cf_template_name] = cf_input_params

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
        for cf_template_name in self.cf_templates:
            if self.cf_resources.get(cf_template_name) is None:
                cf_template_file_name = self._get_cf_template_file_name(cf_template_name)
                pool_size = self._get_resource_pool_size(cf_template_file_name)
                self.cf_resources[cf_template_name] = self.pull_resource_by_template_name(cf_template_name,
                                                                                          pool_size,
                                                                                          constants.wait_time_out_secs)
            resources.append(self.cf_resources[cf_template_name])
        return resources

    def pull_resource_by_template_name(self, cf_template_name, pool_size, time_out_sec):
        """
        Pulls 'AVAILABLE' resources from Dynamo DB table by cloud formation template name,
        if resource is not available it waits.
        :param cf_template_name: The cloud formation template name
        :param time_out_sec: The amount of seconds to wait for resource before time out
        :return: The available resources
        """
        # TODO (semiond): Implement logic to replace create/update
        # resource in case if input parameters does not match for given template:
        # https://issues.amazon.com/issues/Digito-1203
        # TODO: Implement logic to handle DEDICATED/ON_DEMAND resource creation/termination:
        # https://issues.amazon.com/issues/Digito-1204
        # TODO: Implement CF template diff detector to update stack if template changed:
        # https://issues.amazon.com/issues/Digito-1205
        logging.info('Pulling resources for [{}] template'.format(cf_template_name))
        waited_time_sec = 0
        while waited_time_sec < time_out_sec:
            resources = ResourceModel.query(cf_template_name)
            for i in range(pool_size):
                resource = self._filter_resource_by_index(resources, i)
                if resource is None:
                    resource = self._create_resource(i, pool_size, cf_template_name)
                    if resource is not None:
                        return resource
                elif resource.status == ResourceModel.Status.AVAILABLE.name:
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
                            cf_template_name,
                            pool_size,
                            constants.sleep_time_secs)
            time.sleep(constants.sleep_time_secs)
            waited_time_sec = waited_time_sec + constants.sleep_time_secs

        err_message = "Resource retrieving operation timed out in [{}] seconds for [{}] template."\
            .format(time_out_sec, cf_template_name)
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
            ResourceModel.update_resource_status(resource,
                                                 ResourceModel.Status.AVAILABLE)

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

    def _get_resource_pool_size(self, cf_template_name):
        """
        Using config.py finds pool size for given template
        (number of cloud formation stack copies to be created for given cloud formation template).
        :param cf_template_path: The file path to cloud formation template
        :return: The pool size
        """
        pool_size = config.pool_size.get(cf_template_name)
        if pool_size is None:
            default_pool_size = config.pool_size['default']
            logging.warning("Pool size for [%s] template not found, using default: %d",
                            cf_template_name, default_pool_size)
            return default_pool_size
        logging.info("Pool size for [%s] template: %d", cf_template_name, pool_size)
        return pool_size

    def _create_resource(self, index, pool_size, cf_template_name):
        """
        Creates resource for given cloud formation template.
        :param index: The cloud formation template resource index (should not exceed pool_size limit.)
        :param pool_size: The cloud formation pool size.
        :param cf_template_name: The cloud formation template
        :return: The created clkoud formation resources
        """

        cf_stack_name = self._get_cf_template_file_name(cf_template_name) + '-' + str(index)
        cf_template_file = self._get_cf_template_file_path(cf_template_name)

        try:
            resource = ResourceModel.create(
                cf_stack_index=index,
                cf_template_name=cf_template_name,
                pool_size=pool_size,
                cf_stack_name=cf_stack_name,
                status=ResourceModel.Status.CREATING.name,
                leased_on=datetime.now(),
                created_on=datetime.now(),
                updated_on=datetime.now()
            )

            # Creating cloud formation stack stack
            cf_input_params = self.cf_templates.get(cf_template_name)
            logging.info("Creating stack [%s] with input params [%s]", cf_stack_name, cf_input_params)
            cf_template_s3_url = S3.upload_file(cf_template_file)
            cf_output_params = CloudFormationTemplate.deploy_cf_stack(cf_template_s3_url,
                                                                      cf_stack_name, **cf_input_params)

            # Updating record and leasing for waiting thread
            resource.status = ResourceModel.Status.LEASED.name
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

    def _get_cf_template_file_name(self, cf_template_name):
        cf_template_path = self._get_cf_template_file_path(cf_template_name)
        base_name = os.path.basename(cf_template_path)
        (file_name, ext) = os.path.splitext(base_name)
        return file_name

    def _get_cf_template_file_path(self, cf_template_name):
        cf_template_path = config.base_template_dir + cf_template_name
        if not os.path.isfile(cf_template_path):
            raise FileNotFoundError('Cloud formation template with name [{}] does not exist.'.format(cf_template_path))
        return cf_template_path
