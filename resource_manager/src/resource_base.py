import resource_manager.src.constants as constants
import time
import logging
from .resource_model import ResourceModel
from resource_manager.src.cloud_formation import CloudFormationTemplate


class ResourceBase:

    def __init__(self):
        pass

    @staticmethod
    def _delete_resource(resource_to_delete: ResourceModel, cfn_helper: CloudFormationTemplate,
                         logger=logging.getLogger(), all_resources=[]):
        """
        Deletes resource stack and record DynamoDB.
        :param resource_to_delete: Resource to be deleted.
        :param all_resources: All existing resources to check dependencies.
        :param cfn_helper: The cloud formation helper.
        """
        cfn_stack_name = resource_to_delete.cf_stack_name
        sleep_time_secs = constants.cf_operation_sleep_time_secs
        try:
            ResourceModel.update_resource_status(resource_to_delete, ResourceModel.Status.DELETING)
            dependent_stack_name = ResourceBase._get_dependents(cfn_stack_name, all_resources, logger)
            while len(dependent_stack_name) > 0:
                logger.info(f'Waiting for stack(s) [{",".join(dependent_stack_name)}] to be deleted before '
                            f'deleting [{cfn_stack_name}], sleeping [{sleep_time_secs}] seconds.')
                time.sleep(sleep_time_secs)
                dependent_stack_name = ResourceBase._get_dependents(cfn_stack_name, ResourceModel.scan(), logger)

            # Delete stack.
            cfn_helper.delete_cf_stack(cfn_stack_name)
            ResourceModel.update_resource_status(resource_to_delete, ResourceModel.Status.DELETED)
        except Exception as e:
            logger.error(f'Failed to delete [{cfn_stack_name}] stack due to: {e}')
            ResourceModel.update_resource_status(resource_to_delete, ResourceModel.Status.DELETE_FAILED)

    @staticmethod
    def _get_dependents(cfn_stack_name: str, all_resources: [], logger=logging.getLogger()) -> str:
        """
        Returns list of cloud formation dependents for given stack name.
        :param cfn_stack_name: The cfn stack name to find dependents for.
        :param all_resources: The list of all existing resources.
        :param logger: The logger.
        :return: The list of cloud formation dependents for given stack name.
        """
        dependents = []
        for resource in all_resources:
            if resource.cfn_dependency_stacks and cfn_stack_name in resource.cfn_dependency_stacks \
                    and resource.status != ResourceModel.Status.DELETED.name:
                if resource.status == ResourceModel.Status.DELETE_FAILED.name:
                    err_message = f'Stack [{cfn_stack_name}] deletion failed due to dependent ' \
                                  f'stack [{resource.cf_stack_name}] deletion failed.'
                    logger.error(err_message)
                    raise Exception(err_message)
                dependents.append(resource.cf_stack_name)
        return dependents
