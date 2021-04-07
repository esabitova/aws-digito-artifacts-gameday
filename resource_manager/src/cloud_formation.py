import logging
import time
from botocore.exceptions import ClientError
import resource_manager.src.constants as constants
from botocore.config import Config


class CloudFormationTemplate:
    """
    Cloud formation template manipulation functionality.
    """

    def __init__(self, boto3_session):
        config = Config(retries={'max_attempts': 15, 'mode': 'standard'})
        self.client = boto3_session.client('cloudformation', config=config)
        self.resource = boto3_session.resource('cloudformation', config=config)

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
        :return: The cloud formation outupts
        """
        stack = self.resource.Stack(stack_name)
        return stack.outputs

    def _create_cf_stack(self, cf_template_s3_url, stack_name, **kwargs):
        """
        Creates cloud formation stack for given cloud cormation template and inputs.
        :param stack_name: The cloud formation stack name
        :param template_url: The cloud formation template URL located in S3
        :param kwargs: The cloud formation input parameters.
        """
        parameters = self._parse_input_parameters(**kwargs)
        try:
            self._create(stack_name, cf_template_s3_url, parameters)
        except ClientError as e:
            if e.response['Error']['Code'] == 'AlreadyExistsException':
                logging.info('Stack [%s] already exists, updating...', stack_name)
                self._update(stack_name, cf_template_s3_url, parameters)
            else:
                logging.error(e)
                raise e

    def _create(self, stack_name, cf_template_s3_url, parameters):
        """
        Performs cloud formation create stack operation for given parameters.
        :param stack_name The cloud formation stack name.
        :param cf_template_s3_url The cloud formation template URL located in S3
        :param parameters The input parameters for cloud formation stack
        """
        self._wait_stack_operation_completion(stack_name)
        self.client.create_stack(
            StackName=stack_name,
            TemplateURL=cf_template_s3_url,
            Capabilities=['CAPABILITY_IAM'],
            Parameters=parameters)
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
                Parameters=parameters)
            self._wait_stack_operation_completion(stack_name)
        except ClientError as e:
            err_message = e.response['Error']['Message']
            if 'No updates are to be performed.' in err_message and e.response['Error']['Code'] == 'ValidationError':
                logging.info("Stack [{}] already updated.".format(stack_name))
            else:
                logging.error(e)
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
                logging.info("Waiting for stack [%s] event [%s] to be completed, sleeping [%d] seconds.", stack_name,
                             stack_status, constants.cf_operation_sleep_time_secs)
                time.sleep(constants.cf_operation_sleep_time_secs)
                response = self.client.describe_stacks(StackName=stack_name)
                stack_status = response['Stacks'][0]['StackStatus']
        except ClientError:
            # Do nothing as stack doesn't exist.
            # TODO(semiond): Investigate better exception handling: https://issues.amazon.com/issues/Digito-1212
            pass

    def delete_cf_stack(self, stack_name):
        """
        Deletes cloud formation stack which is associated with
        this class instance, waits till completion.
        :param stack_name The stack name to delete.
        """

        self.client.delete_stack(StackName=stack_name)
        waiter = self.client.get_waiter('stack_delete_complete')
        waiter.wait(StackName=stack_name)
