import unittest
import pytest
import resource_manager.src.util.ssm_utils as ssm_utils
import resource_manager.src.util.boto3_client_factory as client_factory
from datetime import datetime
from dateutil.tz import tzlocal
from unittest.mock import MagicMock


@pytest.mark.unit_test
class TestSSMUtils(unittest.TestCase):

    def setUp(self):
        self.session_mock = MagicMock()
        self.mock_ssm_service = MagicMock()
        self.client_side_effect_map = {
            'ssm': self.mock_ssm_service,

        }
        self.session_mock.client.side_effect = lambda service_name, config=None:\
            self.client_side_effect_map.get(service_name)

    def tearDown(self):
        # Clean client factory cache after each test.
        client_factory.clients = {}
        client_factory.resources = {}

    def test_get_ssm_step_interval_success(self):
        expected_end_time = datetime(2021, 4, 8, 15, 4, 38, 212000, tzinfo=tzlocal())
        expected_start_time = datetime(2021, 4, 8, 15, 4, 37, 330000, tzinfo=tzlocal())
        execution_id = 'test_ssm_execution_id'
        step_name = 'test_ssm_step_name'
        self.mock_ssm_service.get_automation_execution.return_value = {'AutomationExecution': {
            'StepExecutions': [
                {'StepName': step_name,
                 'ExecutionEndTime': expected_end_time,
                 'ExecutionStartTime': expected_start_time
                 }
            ]
        }}
        actual_start_time, actual_end_time = ssm_utils.get_ssm_step_interval(self.session_mock, execution_id, step_name)
        self.assertEqual(datetime.utcfromtimestamp(expected_end_time.timestamp()), actual_end_time)
        self.assertEqual(datetime.utcfromtimestamp(expected_start_time.timestamp()), actual_start_time)
        self.mock_ssm_service.get_automation_execution.assert_called_once_with(AutomationExecutionId=execution_id)

    def test_get_ssm_step_interval_no_end_time_success(self):
        expected_start_time = datetime(2021, 4, 8, 15, 4, 37, 330000, tzinfo=tzlocal())
        execution_id = 'test_ssm_execution_id'
        step_name = 'test_ssm_step_name'
        self.mock_ssm_service.get_automation_execution.return_value = {'AutomationExecution': {
            'StepExecutions': [
                {'StepName': step_name,
                 'ExecutionStartTime': expected_start_time
                 }
            ]
        }}
        actual_start_time, actual_end_time = ssm_utils.get_ssm_step_interval(self.session_mock, execution_id, step_name)
        self.assertIsNone(actual_end_time)
        self.assertEqual(datetime.utcfromtimestamp(expected_start_time.timestamp()), actual_start_time)
        self.mock_ssm_service.get_automation_execution.assert_called_once_with(AutomationExecutionId=execution_id)

    def test_get_ssm_step_interval_bad_step_fail(self):
        execution_id = 'test_ssm_execution_id'
        step_name = 'bad_step_name'
        self.mock_ssm_service.get_automation_execution.return_value = {'AutomationExecution': {
            'StepExecutions': [
                {'StepName': 'good_step_name'}
            ]
        }}
        self.assertRaises(Exception, ssm_utils.get_ssm_step_interval, self.session_mock, execution_id, step_name)
        self.mock_ssm_service.get_automation_execution.assert_called_once_with(AutomationExecutionId=execution_id)

    def test_ssm_step_status_success(self):
        execution_id = 'test_ssm_execution_id'
        step_name = 'test_ssm_step_name'
        expected_step_status = 'Success'
        self.mock_ssm_service.get_automation_execution.return_value = {'AutomationExecution': {
            'StepExecutions': [
                {'StepName': step_name,
                 'StepStatus': expected_step_status,

                 }
            ]
        }}
        actual_status = ssm_utils.get_ssm_step_status(self.session_mock, execution_id, step_name)
        self.assertEqual(expected_step_status, actual_status)
        self.mock_ssm_service.get_automation_execution.assert_called_once_with(AutomationExecutionId=execution_id)

    def test_ssm_step_status_bad_step_fail(self):
        execution_id = 'test_ssm_execution_id'
        step_name = 'bad_step_name'
        expected_step_status = 'Success'
        self.mock_ssm_service.get_automation_execution.return_value = {'AutomationExecution': {
            'StepExecutions': [
                {'StepName': 'goo_step_name',
                 'StepStatus': expected_step_status,

                 }
            ]
        }}
        self.assertRaises(Exception, ssm_utils.get_ssm_step_status, self.session_mock, execution_id, step_name)
        self.mock_ssm_service.get_automation_execution.assert_called_once_with(AutomationExecutionId=execution_id)

    def test_send_step_approval_approve_success(self):
        execution_id = 'test_ssm_execution_id'
        ssm_utils.send_step_approval(self.session_mock, execution_id)
        self.mock_ssm_service.send_automation_signal.assert_called_once_with(AutomationExecutionId=execution_id,
                                                                             SignalType='Approve')

    def test_send_step_approval_reject_success(self):
        execution_id = 'test_ssm_execution_id'
        ssm_utils.send_step_approval(self.session_mock, execution_id, is_approved=False)
        self.mock_ssm_service.send_automation_signal.assert_called_once_with(AutomationExecutionId=execution_id,
                                                                             SignalType='Reject')
