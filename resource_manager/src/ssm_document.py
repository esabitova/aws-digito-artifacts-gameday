import logging
import time
import resource_manager.src.constants as constants
import resource_manager.src.util.param_utils as param_utils
from sttable import parse_str_table


class SsmDocument:
    """
    Class for SSM automation document manipulation.
    """

    def __init__(self, boto3_session):
        self.ssm_client = boto3_session.client('ssm')
        self.region = boto3_session.region_name

    def execute(self, document_name, input_params):
        """
         Executes SSM document for given document name and input parameters.
        :param document_name: The SSM document name
        :param input_params: The SSM document input parameters
        :return: The SSM execution final status
        """
        if self._document_exists(document_name):
            logging.info("Executing SSM document [%s] with parameters: [%s]", document_name, input_params)
            # Executing SSM document
            execution_id = self.ssm_client.start_automation_execution(
                DocumentName=document_name,
                # DocumentVersion=version,
                Parameters=input_params
            )['AutomationExecutionId']
            logging.info(f'SSM execution URL: {self._build_execution_url(execution_id, None, None)}')
            return execution_id
        else:
            error_msg = "SSM document with name [{}] does not exist.".format(document_name)
            logging.error(error_msg)
            raise Exception(error_msg)

    def wait_for_execution_completion(self, execution_id, document_name):
        """
        Returns SSM document final execution status, if status is in PROGRESS/PENDING
        it will wait till SSM document execution will be completed.
        :param execution_id: The SSM document execution id
        :param document_name: The SSM document name
        :return: The SSM document execution status.
        """
        # Fetch ssm execution status
        status = self._get_execution_status(execution_id, document_name)

        # Wait for execution to be completed
        while status == 'InProgress' or status == 'Pending' or status == 'Cancelling' or status == 'Waiting':
            time.sleep(constants.sleep_time_secs)
            status = self._get_execution_status(execution_id, document_name)
        return status

    def wait_for_execution_step_status_is_terminal_or_waiting(self, execution_id, document_name, step_name, time_to_wait):
        """
        Returns execution step final status or WAITING, if step is in PROGRESS/PENDING status
        it will wait till step execution will be completed starts waiting for approval.
        :param execution_id: The SSM document execution id
        :param document_name: The SSM document name
        :param step_name: The SSM document execution step name
        :param time_to_wait: Time in seconds to wait until step status is resolved
        :return: The SSM document execution status.
        """
        start_time = time.time()
        step_status = self._get_execution_step_status(execution_id, step_name)
        elapsed_time = time.time() - start_time

        # Wait for execution step to resolve in waiting or one of terminating statuses
        while step_status == 'InProgress' or step_status == 'Pending' or step_status == 'Cancelling':
            if elapsed_time > time_to_wait:
                logging.exception(f'Execution step {step_name} for document {document_name} timed out')
                return 'WaitTimedOut'
            time.sleep(constants.sleep_time_secs)
            step_status = self._get_execution_step_status(execution_id, step_name)
            elapsed_time = time.time() - start_time
        return step_status

    def parse_input_parameters(self, cf_output, cache, input_parameters):
        """
        Function to parse given SSM document input parameters based. Parameters could be of 3 types:
        * cached - in case if given parameter value is pointing to cache (Example: {{cache:valueKeyA>valueKeyB}})
        * cloud formation output - in case if given parameter value is pointing to cloud
        formation output (Example: {{output:paramNameA}})
        * simple value - in case if given parameter value is simple value
        :param cf_output - The CFN outputs
        :param cache - The cache, used to get cached values by given keys.
        :param input_parameters - The SSM input parameters as described in scenario feature file.
        """
        input_params = parse_str_table(input_parameters).rows[0]
        parameters = {}
        for param, param_val_ref in input_params.items():
            value = param_utils.parse_param_value(param_val_ref, {'cache': cache, 'cfn-output': cf_output})
            parameters[param] = [str(value)]
        return parameters

    def _get_execution_status(self, execution_id, document_name):
        """
        Returns SSM document execution status for given execution id.
        :param execution_id: The SSM document execution id
        :param document_name: The SSM document name
        :return: The SSM document execution status
        """
        execution = self.ssm_client.get_automation_execution(
            AutomationExecutionId=execution_id
        )
        step_executions = execution['AutomationExecution']['StepExecutions']
        step = self._get_step_by_status(step_executions, 'InProgress')
        if step:
            step_name = step['StepName']
            step_execution_id = step['StepExecutionId']
            step_index = self._get_step_execution_index(step_executions, step_name)
            logging.info(f'Waiting SSM document step [{document_name}>{step_name}] to be completed: '
                         f'{self._build_execution_url(execution_id, step_index, step_execution_id)}')
        return execution['AutomationExecution']['AutomationExecutionStatus']

    def _get_execution_step_status(self, execution_id, step_name):
        """
        Returns execution step status for given execution id and step name.
        :param execution_id: The SSM document execution id
        :param step_name: The SSM document step name
        :return: The execution step status
        """
        execution = self.ssm_client.get_automation_execution(
            AutomationExecutionId=execution_id
        )
        step_executions = execution['AutomationExecution']['StepExecutions']
        step = self._get_step_by_name(step_executions, step_name)
        return step['StepStatus']

    def _get_step_by_status(self, steps, status):
        """
         Returns SSM document step by given status.
        :param steps: The SSM document execution steps
        :param status: The SSM document execution step status
        :return: The The SSM document execution step for given status
        """
        if steps:
            for s in steps:
                if s['StepStatus'] == status:
                    return s

    def _get_step_by_name(self, steps, step_name):
        """
         Returns SSM document step by a given name.
        :param steps: The SSM document execution steps
        :param step_name: The SSM document execution step name
        :return: The The SSM document execution step for given status
        """
        if steps:
            for s in steps:
                if s['StepName'] == step_name:
                    return s

    def _document_exists(self, document_name):
        """
         Returns True if SSM document for given name exist, False otherwise.
        :param document_name: The SSM automation document name
        :return: True is exist, False otherwise
        """
        return len(self.ssm_client.list_document_versions(Name=document_name)['DocumentVersions']) >= 1

    def _build_execution_url(self, execution_id, step_index, step_execution_id):
        """
        Build and return URL of SSM Automation Execution page
        :param execution_id: The SSM document execution id
        :param step_index The step sequence index in SSM document
        :param step_execution_id: The SSM document step execution id
        :return: Built URL of Automation Execution page
        """
        if step_execution_id is None:
            return f'https://{self.region}.console.aws.amazon.com/systems-manager/automation/execution/{execution_id}'
        return f'https://{self.region}.console.aws.amazon.com/systems-manager/automation/execution/{execution_id}' \
               f'/step/{step_index}/{step_execution_id}'

    def _get_step_execution_index(self, step_executions: [], step_name):
        """
        Returns SSM document step execution sequence index
        :param step_executions The list of SSM document step executions
        :param step_name The name of step execution to find index for
        """
        index = 1
        for step_execution in step_executions:
            if step_name == step_execution['StepName']:
                return index
            index += 1

    def send_step_approval(self, execution_id, is_approved=True):
        """
        Sends approve or reject to SSM execution
        :param execution_id The SSM document execution id
        :param is_approved True if approve, False if reject
        """
        signal_type = 'Approve' if is_approved else 'Reject'
        self.ssm_client.send_automation_signal(
            AutomationExecutionId=execution_id,
            SignalType=signal_type
        )

