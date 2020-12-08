import unittest
import pytest
from unittest.mock import patch, MagicMock, call
from resource_manager.src.ssm_document import SsmDocument


@pytest.mark.unit_test
class TestSsmDocument(unittest.TestCase):
    def setUp(self):
        self.client_patcher = patch('boto3.client')
        self.client = self.client_patcher.start()
        self.mock_ssm = MagicMock()
        self.client_side_effect_map = {
            'ssm': self.mock_ssm
        }
        self.client.side_effect = lambda service_name: self.client_side_effect_map.get(service_name)

    def tearDown(self):
        self.client_patcher.stop()

    def test_execute_not_existing_document_fail(self):
        self.assertRaises(Exception, SsmDocument().execute, 'test_document_name', {'test_param_1': ['test_value_1']})

    def test_wait_for_execution_completion(self):
        execution_1 = {'AutomationExecution':
                       {'StepExecutions': [{'StepStatus': 'InProgress',
                                           'StepName': 'test_step',
                                            'StepExecutionId': '11111'}],
                        'AutomationExecutionStatus': 'InProgress'}}
        execution_2 = {'AutomationExecution':
                       {'StepExecutions': [{'StepStatus': 'InProgress',
                                           'StepName': 'test_step',
                                            'StepExecutionId': '11111'}],
                        'AutomationExecutionStatus': 'Pending'}}
        execution_3 = {'AutomationExecution':
                       {'StepExecutions': [{'StepStatus': 'InProgress',
                                           'StepName': 'test_step',
                                            'StepExecutionId': '11111'}],
                        'AutomationExecutionStatus': 'Completed'}}

        self.mock_ssm.get_automation_execution.side_effect = [execution_1, execution_2, execution_3]

        status = SsmDocument().wait_for_execution_completion('123456', 'test_document_name')

        self.mock_ssm.get_automation_execution.assert_has_calls([call(AutomationExecutionId='123456'),
                                                                 call(AutomationExecutionId='123456'),
                                                                 call(AutomationExecutionId='123456')])

    def test_execute_success(self):
        self.mock_ssm.list_documents.return_value = {'DocumentIdentifiers': ['test_document_name']}
        self.mock_ssm.start_automation_execution.return_value = {'AutomationExecutionId': '123456'}
        execution_id = SsmDocument().execute('test_document_name', {'test_param_1': ['test_value_1']})
        self.assertEqual('123456', execution_id)
        self.mock_ssm.start_automation_execution.assert_called_once()

