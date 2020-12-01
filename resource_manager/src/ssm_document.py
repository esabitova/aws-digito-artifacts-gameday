import boto3
import logging
import time
import resource_manager.src.constants as constants


class SsmDocument:
    """
    Class for SSM automation document manipulation.
    """

    def __init__(self):
        self.ssm_client = boto3.client('ssm')

    def execute(self, document_name, input_params):
        """
         Execcutes SSM document for gievn document name and input paramaters.
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
            return self._wait_for_execution_completion(execution_id, document_name)
        else:
            error_msg = "SSM document with name [{}] does not exist.".format(document_name)
            logging.error(error_msg)
            raise Exception(error_msg)

    def _wait_for_execution_completion(self, execution_id, document_name):
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
        while status == 'InProgress' or status == 'Pending':
            time.sleep(constants.sleep_time_secs)
            status = self._get_execution_status(execution_id, document_name)
        return status

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
        return len(self.ssm_client.list_documents(DocumentFilterList=[{'key': 'Name', 'value': document_name}])
                   ['DocumentIdentifiers']) == 1
