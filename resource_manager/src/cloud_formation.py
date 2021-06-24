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

    def deploy_cf_stack(self, cfn_template_s3_url, stack_name, **kwargs):
        """
        Deploys cloud formation stack by given cloud formation template
        file name and input parameters.
        :param cfn_template_s3_url The S3 cloud formation template location url.
        :param stack_name The cloud formation stack name.
        :param kwargs The cloud formation input parameters.
        """

        self._create_cf_stack(cfn_template_s3_url, stack_name, **kwargs)
        return self._get_cf_stack_outputs(stack_name)

    def _get_cf_stack_outputs(self, stack_name):
        """
        Returns cloud formation stack outputs, which is
        associated with this class instance, to be used as SSM automation documents inputs.
        :return: The cloud formation outputs
        """
        stack = self.resource.Stack(stack_name)
        return stack.outputs

    def _create_cf_stack(self, cf_template_s3_url, stack_name, **kwargs):
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

    def _create(self, stack_name, cf_template_s3_url, parameters):
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

    def _update(self, stack_name, cf_template_s3_url, parameters):
        """
        Performs cloud formation update stack operation for given parameters.
        :param stack_name The cloud formation stack name.
        :param cf_template_s3_url The cloud formation template URL located in S3
        :param parameters The input parameters for cloud formation stack
        """
        try:
            self.client.update_stack(
                StackName=stack_name,
                Capabilities=['CAPABILITY_IAM'],
                TemplateURL=cf_template_s3_url,
                UsePreviousTemplate=False,
                Parameters=parameters)
            self._wait_stack_operation_completion(stack_name)
        except ClientError as e:
            err_message = e.response['Error']['Message']
            if e.response['Error']['Code'] == 'ValidationError':
                if 'No updates are to be performed.' in err_message:
                    self.logger.info(f'Stack [{stack_name}] already updated.')
                elif 'is in ROLLBACK_COMPLETE state and can not be updated.' in err_message:
                    self.logger.warning(e)
                    self.delete_cf_stack(stack_name)
                    self._create(stack_name, cf_template_s3_url, parameters)
            else:
                self.logger.error(e)
                raise e

    def _update_termination_protection(self, stack_name, enable_termination_protection):
        """
        Updated the given stack's termination protection
        :param stack_name The cloud formation stack name.
        :param enable_termination_protection boolean value indicating whether or not to enable termination protection
        """
        try:
            self.client.update_termination_protection(StackName=stack_name,
                                                      EnableTerminationProtection=enable_termination_protection)
        except ClientError as e:
            err_message = e.response['Error']['Message']
            if f'Stack [{stack_name}] does not exist' in err_message \
                    and e.response['Error']['Code'] == 'ValidationError':
                # Do nothing as stack for given name does not exist.
                pass
            else:
                self.logger.error(e)
                raise e

    def _parse_input_parameters(self, **kwargs):
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

    def _wait_stack_operation_completion(self, stack_name):
        """
        Waits for stack operation to be completed. It could be CREATE/UPDATE/DELETE and other possible operations.
        :param stack_name The cloud formation stack name
        """
        try:
            response = self.client.describe_stacks(StackName=stack_name)
            stack_status = response['Stacks'][0]['StackStatus']
            while not stack_status or 'IN_PROGRESS' in stack_status:
                self.logger.info("Waiting for stack [%s] event [%s] to be completed, sleeping [%d] seconds.",
                                 stack_name, stack_status, constants.cf_operation_sleep_time_secs)
                time.sleep(constants.cf_operation_sleep_time_secs)
                response = self.client.describe_stacks(StackName=stack_name)
                stack_status = response['Stacks'][0]['StackStatus']
                if 'FAILED' in stack_status or 'ROLLBACK_COMPLETE' in stack_status:
                    raise Exception(f'Stack for name [{stack_name}] failed with status [{stack_status}].')
        except ClientError as e:
            err_message = e.response['Error']['Message']
            if f'Stack with id {stack_name} does not exist' in err_message and \
                    e.response['Error']['Code'] == 'ValidationError':
                # Do nothing as stack doesn't exist.
                pass
            else:
                self.logger.error(e)
                raise e

    def delete_cf_stack(self, stack_name):
        """
        Deletes cloud formation stack which is associated with
        this class instance, waits till completion.
        :param stack_name The stack name to delete.
        """
        self.logger.info(f'Deleting [{stack_name}] stack.')
        self._update_termination_protection(stack_name, False)
        self.client.delete_stack(StackName=stack_name)
        self._wait_stack_operation_completion(stack_name)

    def describe_cf_stack(self, stack_name):
        return self.client.describe_stacks(StackName=stack_name)['Stacks'][0]

    def describe_cf_stack_events(self, stack_name):
        res = self.client.describe_stack_events(StackName=stack_name)
        resources = res['StackEvents']
        while 'NextToken' in res:
            res = self.client.describe_stack_events(StackName=stack_name, NextToken=res['NextToken'])
            resources.extend(res['StackEvents'])
        return resources
