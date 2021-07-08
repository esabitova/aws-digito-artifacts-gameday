import logging
import time
import resource_manager.src.constants as constants
from botocore.exceptions import ClientError
from .util.boto3_client_factory import client, resource


class CloudFormationTemplate:
    """
    Cloud formation template manipulation functionality.
    """

    def __init__(self, boto3_session, logger=logging.getLogger()):
        self.client = client('cloudformation', boto3_session)
        self.resource = resource('cloudformation', boto3_session)
        self.logger = logger

    def deploy_cf_stack(self, cfn_template_s3_url: str, stack_name: str, **kwargs) -> []:
        """
        Deploys cloud formation stack by given cloud formation template
        file name and input parameters.
        :param cfn_template_s3_url The S3 cloud formation template location url.
        :param stack_name The cloud formation stack name.
        :param kwargs The cloud formation input parameters.
        """

        self._create_cf_stack(cfn_template_s3_url, stack_name, **kwargs)
        return self._get_cf_stack_outputs(stack_name)

    def _get_cf_stack_outputs(self, stack_name: str) -> []:
        """
        Returns cloud formation stack outputs, which is
        associated with this class instance, to be used as SSM automation documents inputs.
        :return: The cloud formation outputs
        """
        return self.resource.Stack(stack_name).outputs

    def _create_cf_stack(self, cf_template_s3_url: str, stack_name: str, **kwargs):
        """
        Creates cloud formation stack for given cloud formation template and inputs.
        :param stack_name: The cloud formation stack name
        :param template_url: The cloud formation template URL located in S3
        :param kwargs: The cloud formation input parameters.
        """
        parameters = self._parse_input_parameters(**kwargs)
        try:
            self._create(stack_name, cf_template_s3_url, parameters)
        except ClientError as e:
            if e.response['Error']['Code'] == 'AlreadyExistsException':
                self._update(stack_name, cf_template_s3_url, parameters)
            else:
                self.logger.error(e)
                raise e

    def _create(self, stack_name: str, cf_template_s3_url: str, parameters: []):
        """
        Performs cloud formation create stack operation for given parameters.
        :param stack_name The cloud formation stack name.
        :param cf_template_s3_url The cloud formation template URL located in S3
        :param parameters The input parameters for cloud formation stack
        """
        self.logger.info(f'Creating [{stack_name}] stack.')
        self._wait_stack_operation_completion(stack_name)
        self.client.create_stack(
            StackName=stack_name,
            TemplateURL=cf_template_s3_url,
            Capabilities=['CAPABILITY_IAM'],
            Parameters=parameters,
            EnableTerminationProtection=True)
        self._wait_stack_operation_completion(stack_name)

    def _update(self, stack_name: str, cf_template_s3_url: str, parameters: []):
        """
        Performs cloud formation update stack operation for given parameters.
        :param stack_name The cloud formation stack name.
        :param cf_template_s3_url The cloud formation template URL located in S3
        :param parameters The input parameters for cloud formation stack
        """
        try:
            if 'ROLLBACK_COMPLETE' in self._get_stack_status(stack_name):
                self.logger.warning(f'Stack [{stack_name}] is in [ROLLBACK_COMPLETE] state and can not be updated. '
                                    f'Recreating stack.')
                self.delete_cf_stack(stack_name)
                self._create(stack_name, cf_template_s3_url, parameters)
            else:
                self.client.update_stack(
                    StackName=stack_name,
                    Capabilities=['CAPABILITY_IAM'],
                    TemplateURL=cf_template_s3_url,
                    UsePreviousTemplate=False,
                    Parameters=parameters)
                self._wait_stack_operation_completion(stack_name)
        except ClientError as e:
            err_message = e.response['Error']['Message']
            if e.response['Error']['Code'] == 'ValidationError' \
                    and 'No updates are to be performed.' in err_message:
                self.logger.info(f'Stack [{stack_name}] already updated.')
            else:
                self.logger.error(e)
                raise e

    def _update_termination_protection(self, stack_name: str, enable: bool):
        """
        Updated the given stack's termination protection
        :param stack_name The cloud formation stack name.
        :param enable The value indicating whether or not to enable termination protection
        """
        try:
            self.client.update_termination_protection(StackName=stack_name, EnableTerminationProtection=enable)
        except ClientError as e:
            err_message = e.response['Error']['Message']
            if e.response['Error']['Code'] == 'ValidationError' \
                    and f'Stack [{stack_name}] does not exist' in err_message:
                # Do nothing as stack for given name does not exist.
                pass
            else:
                self.logger.error(e)
                raise e

    def _parse_input_parameters(self, **kwargs) -> []:
        """
        Parsing parameters to be passed to cloud formation stack as cloud formation stack expects.
        :param **kwargs The arguments to be parsed as cloud formation input parameters
        """
        parameters = []
        for prop in kwargs.items():
            parameter = {
                'ParameterKey': prop[0],
                'ParameterValue': prop[1]
            }
            parameters.append(parameter)
        return parameters

    def _wait_stack_operation_completion(self, stack_name: str):
        """
        Waits for stack operation to be completed. It could be CREATE/UPDATE/DELETE and other possible operations.
        :param stack_name The cloud formation stack name
        """
        try:
            stack_status = self._get_stack_status(stack_name)
            while 'IN_PROGRESS' in stack_status:
                self.logger.info("Waiting for stack [%s] event [%s] to be completed, sleeping [%d] seconds.",
                                 stack_name, stack_status, constants.cf_operation_sleep_time_secs)
                time.sleep(constants.cf_operation_sleep_time_secs)
                stack_status = self._get_stack_status(stack_name)
                if 'FAILED' in stack_status or 'ROLLBACK_COMPLETE' in stack_status:
                    raise Exception(f'Stack for name [{stack_name}] failed with status [{stack_status}].')
        except ClientError as e:
            err_message = e.response['Error']['Message']
            if e.response['Error']['Code'] == 'ValidationError' \
                    and f'Stack with id {stack_name} does not exist' in err_message:
                # Do nothing as stack doesn't exist.
                pass
            else:
                self.logger.error(e)
                raise e

    def delete_cf_stack(self, stack_name: str):
        """
        Deletes cloud formation stack which is associated with
        this class instance, waits till completion.
        :param stack_name The stack name to delete.
        """
        self.logger.info(f'Deleting [{stack_name}] stack.')
        self._update_termination_protection(stack_name, False)
        self.client.delete_stack(StackName=stack_name)
        self._wait_stack_operation_completion(stack_name)

    def describe_cf_stack(self, stack_name: str) -> {}:
        """
        Returns cloud formation stack information for given stack name.
        :param stack_name: The cloud formation stack name.
        :return: The cloud formation stack information.
        """
        return self.client.describe_stacks(StackName=stack_name)['Stacks'][0]

    def describe_cf_stack_events(self, stack_name: str) -> []:
        """
        Returns cloud formation stack events list for given stack name.
        :param stack_name: The cloud formation stack name.
        :return: The stack events list.
        """
        res = self.client.describe_stack_events(StackName=stack_name)
        resources = res['StackEvents']
        while 'NextToken' in res:
            res = self.client.describe_stack_events(StackName=stack_name, NextToken=res['NextToken'])
            resources.extend(res['StackEvents'])
        return resources

    def _get_stack_status(self, stack_name: str) -> str:
        """
        Returns cloud formation stack status for given stack name.
        :param stack_name: The cloud formation stack name.
        :return: The stack status.
        """
        return self.resource.Stack(stack_name).stack_status

    def stack_exists(self, stack_name: str, required_status='DELETE_COMPLETE'):
        """
        Verifies if cfn stack for given name exist.
        :param stack_name: The cfn stack name to verify
        :param required_status: The required status in case if stack is till exist.
        :return: True  stack exists, False otherwise.
        """
        try:
            stacks_summary = self.client.describe_stacks(StackName=stack_name)
            stack_info = stacks_summary.get('Stacks')[0]
            return stack_name == stack_info.get('StackName') and stack_info.get('StackStatus') != required_status
        except ClientError as e:
            stack_not_found_error = f'Stack with id {stack_name} does not exist'
            error_received = e.response['Error']
            error_code_received = error_received.get('Code')
            error_message_received = error_received.get('Message')
            if error_code_received == 'ValidationError' and error_message_received == stack_not_found_error:
                return False
            self.logger.exception(f'Client error while describing stacks: {e}')
            raise
        except Exception:
            self.logger.exception('Error while checking stack')
            raise
