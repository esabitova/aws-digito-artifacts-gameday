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
            logging.info(f'SSM execution URL: {self._build_execution_url(execution_id)}')
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
        while status == 'InProgress' or status == 'Pending' or status == 'Cancelling':
            time.sleep(constants.sleep_time_secs)
            status = self._get_execution_status(execution_id, document_name)
        return status

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
        step = self._get_step_by_status(execution['AutomationExecution']['StepExecutions'], 'InProgress')
        if step:
            logging.info('[%s(id:%s)] Waiting SSM document step [%s(id:%s)] to be completed',
                         document_name,
                         execution_id,
                         step['StepName'],
                         step['StepExecutionId'])
        return execution['AutomationExecution']['AutomationExecutionStatus']

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

    def _document_exists(self, document_name):
        """
         Returns True if SSM document for given name exist, False otherwise.
        :param document_name: The SSM automation document name
        :return: True is exist, False otherwise
        """
        return len(self.ssm_client.list_document_versions(Name=document_name)['DocumentVersions']) == 1

    def _build_execution_url(self, execution_id):
        """
        Build and return URL of SSM Automation Execution page
        :param execution_id: The SSM document execution id
        :return: Built URL of Automation Execution page
        """
        return f'https://{self.region}.console.aws.amazon.com/systems-manager/automation/execution/{execution_id}'
