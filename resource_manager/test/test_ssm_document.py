import unittest
from typing import List
from unittest.mock import MagicMock, call, patch

import pytest

import resource_manager.src.constants as constants
import resource_manager.src.util.boto3_client_factory as client_factory
from resource_manager.test.util.mock_sleep import MockSleep
from resource_manager.src.ssm_document import SsmDocument

SSM_EXECUTION_ID = '123456'
SSM_OUTPUT_KEY = 'RollbackExecutionId'
SSM_OUTPUT_VALUE = '654321'
SSM_DOCUMENT_NAME = 'document-name'
SSM_STEP_NAME = 'step-name'


def prepare_execution_description(step_name, status):
    return {
        'AutomationExecution':
            {
                'DocumentName': SSM_DOCUMENT_NAME,
                'AutomationExecutionStatus': status,
                'StepExecutions': [
                    {
                        'StepStatus': status,
                        'StepName': step_name,
                        'StepExecutionId': '11111',
                        'Outputs': {
                            SSM_OUTPUT_KEY: [SSM_OUTPUT_VALUE]
                        }
                    }
                ]
            }
    }


def prepare_execution_description_with_multiple_steps():
    initial: dict = {
        'AutomationExecution':
            {
                'DocumentName': SSM_DOCUMENT_NAME,
                'AutomationExecutionStatus': 'Success',
                'StepExecutions': []
            }
    }
    step_executions: List = initial['AutomationExecution']['StepExecutions']
    for i in range(1, 5):
        step_executions.append({
            'StepStatus': 'Success',
            'StepName': str(i),
            'StepExecutionId': '11111',
            'Outputs': {
                SSM_OUTPUT_KEY: [SSM_OUTPUT_VALUE]
            }
        }
        )
    step_executions.append({
        'StepStatus': 'Failed',
        'StepName': '5',
        'StepExecutionId': '11111',
        'Outputs': {
            SSM_OUTPUT_KEY: [SSM_OUTPUT_VALUE]
        }
    }
    )

    return initial


@pytest.mark.unit_test
class TestSsmDocument(unittest.TestCase):
    def setUp(self):
        self.region_name = 'test_region'
        self.mock_session = MagicMock()
        self.mock_session.configure_mock(name='test_session', region_name=self.region_name)
        self.mock_ssm = MagicMock()
        self.mock_ssm.configure_mock(name='test_ssm')
        self.client_side_effect_map = {
            'ssm': self.mock_ssm
        }
        self.mock_session.client.side_effect = lambda service_name, config=None: \
            self.client_side_effect_map.get(service_name)
        self.ssm_document = SsmDocument(self.mock_session)

    def tearDown(self):
        # Clean client factory cache after each test.
        client_factory.clients = {}
        client_factory.resources = {}

    def test_execute_not_existing_document_fail(self):
        self.assertRaises(Exception, self.ssm_document.execute, 'test_document_name',
                          {'test_param_1': ['test_value_1']})

    @patch('time.sleep')
    @patch('time.time')
    def test_wait_for_execution_completion(self, patched_time, patched_sleep):
        mock_sleep = MockSleep()
        patched_time.side_effect = mock_sleep.time
        patched_sleep.side_effect = mock_sleep.sleep

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

        status = self.ssm_document.wait_for_execution_completion('123456', 'test_document_name')
        self.assertEqual('Completed', status)
        self.mock_ssm.get_automation_execution.assert_has_calls([call(AutomationExecutionId='123456'),
                                                                 call(AutomationExecutionId='123456'),
                                                                 call(AutomationExecutionId='123456')])

    def test_execute_success(self):
        self.mock_ssm.list_document_versions.return_value = {'DocumentVersions': ['test_document_name']}
        self.mock_ssm.start_automation_execution.return_value = {'AutomationExecutionId': '123456'}
        execution_id = self.ssm_document.execute('test_document_name', {'test_param_1': ['test_value_1']})
        self.assertEqual('123456', execution_id)
        self.mock_ssm.start_automation_execution.assert_called_once()

    # Test wait_for_execution_step_status_is_terminal_or_waiting
    @patch('time.sleep')
    @patch('time.time')
    def test_wait_for_execution_step_status_is_terminal_or_waiting_success(self, patched_time, patched_sleep):
        mock_sleep = MockSleep()
        patched_time.side_effect = mock_sleep.time
        patched_sleep.side_effect = mock_sleep.sleep

        execution_1 = prepare_execution_description(SSM_STEP_NAME, 'InProgress')
        execution_2 = prepare_execution_description(SSM_STEP_NAME, 'InProgress')
        execution_3 = prepare_execution_description(SSM_STEP_NAME, 'Success')

        self.mock_ssm.get_automation_execution.side_effect = [execution_1, execution_2, execution_3]

        status = self.ssm_document.wait_for_execution_step_status_is_terminal_or_waiting(
            SSM_EXECUTION_ID, SSM_DOCUMENT_NAME, SSM_STEP_NAME, 10
        )
        self.assertEqual("Success", status)

    @patch('time.sleep')
    @patch('time.time')
    def test_wait_for_execution_step_status_is_terminal_or_waiting_waiting(self, patched_time, patched_sleep):
        mock_sleep = MockSleep()
        patched_time.side_effect = mock_sleep.time
        patched_sleep.side_effect = mock_sleep.sleep

        execution_1 = prepare_execution_description(SSM_STEP_NAME, 'InProgress')
        execution_2 = prepare_execution_description(SSM_STEP_NAME, 'InProgress')
        execution_3 = prepare_execution_description(SSM_STEP_NAME, 'Waiting')

        self.mock_ssm.get_automation_execution.side_effect = [execution_1, execution_2, execution_3]

        status = self.ssm_document.wait_for_execution_step_status_is_terminal_or_waiting(
            SSM_EXECUTION_ID, SSM_DOCUMENT_NAME, SSM_STEP_NAME, 10
        )
        self.assertEqual("Waiting", status)

    @patch('time.sleep')
    @patch('time.time')
    def test_wait_for_execution_step_status_is_terminal_or_waiting_timeout(self, patched_time, patched_sleep):
        mock_sleep = MockSleep()
        patched_time.side_effect = mock_sleep.time
        patched_sleep.side_effect = mock_sleep.sleep

        self.mock_ssm.get_automation_execution.return_value = prepare_execution_description(SSM_STEP_NAME, 'InProgress')

        status = self.ssm_document.wait_for_execution_step_status_is_terminal_or_waiting(
            SSM_EXECUTION_ID, SSM_DOCUMENT_NAME, SSM_STEP_NAME, 10
        )
        self.assertEqual("WaitTimedOut", status)

    @patch('time.sleep')
    @patch('time.time')
    def test_wait_for_execution_step_status_is_in_progress(self, patched_time, patched_sleep):
        mock_sleep = MockSleep()
        patched_time.side_effect = mock_sleep.time
        patched_sleep.side_effect = mock_sleep.sleep

        execution_1 = prepare_execution_description(SSM_STEP_NAME, 'Pending')
        execution_2 = prepare_execution_description(SSM_STEP_NAME, 'Pending')
        execution_3 = prepare_execution_description(SSM_STEP_NAME, 'InProgress')

        self.mock_ssm.get_automation_execution.side_effect = [execution_1, execution_2, execution_3]

        status = self.ssm_document.wait_for_execution_step_status_is_in_progress(
            SSM_EXECUTION_ID, SSM_DOCUMENT_NAME, SSM_STEP_NAME, 10
        )
        self.assertEqual("InProgress", status)

    @patch('time.sleep')
    @patch('time.time')
    def test_wait_for_execution_step_status_is_in_progress_timeout(self, patched_time, patched_sleep):
        mock_sleep = MockSleep()
        patched_time.side_effect = mock_sleep.time
        patched_sleep.side_effect = mock_sleep.sleep

        self.mock_ssm.get_automation_execution.return_value = prepare_execution_description(SSM_STEP_NAME, 'Pending')

        status = self.ssm_document.wait_for_execution_step_status_is_in_progress(
            SSM_EXECUTION_ID, SSM_DOCUMENT_NAME, SSM_STEP_NAME, 10
        )
        self.assertEqual("WaitTimedOut", status)

    def test_get_step_output(self):
        self.mock_ssm.get_automation_execution.return_value = prepare_execution_description(SSM_STEP_NAME, 'Success')

        output = self.ssm_document.get_step_output(SSM_EXECUTION_ID, SSM_STEP_NAME, SSM_OUTPUT_KEY)
        self.assertEqual(SSM_OUTPUT_VALUE, output)

    @patch('time.sleep')
    @patch('time.time')
    def test_cancel_execution_with_rollback_with_rollback_step_success(self, patched_time, patched_sleep):
        mock_sleep = MockSleep()
        patched_time.side_effect = mock_sleep.time
        patched_sleep.side_effect = mock_sleep.sleep

        execution_1 = prepare_execution_description(constants.rollback_step_name, 'Success')
        execution_2 = prepare_execution_description(constants.rollback_step_name, 'Success')
        execution_3 = prepare_execution_description(SSM_STEP_NAME, 'InProgress')
        execution_4 = prepare_execution_description(SSM_STEP_NAME, 'Success')
        self.mock_ssm.get_automation_execution.side_effect = [execution_1, execution_2, execution_3, execution_4]
        self.ssm_document.cancel_execution_with_rollback('test_execution_id')
        self.mock_ssm.stop_automation_execution.assert_called_once()
        self.mock_ssm.get_automation_execution.assert_has_calls([call(AutomationExecutionId='test_execution_id'),
                                                                 call(AutomationExecutionId='test_execution_id'),
                                                                 call(AutomationExecutionId=SSM_OUTPUT_VALUE),
                                                                 call(AutomationExecutionId=SSM_OUTPUT_VALUE)])
        self.assertEqual(self.mock_ssm.get_automation_execution.call_count, 4)

    @patch('time.sleep')
    @patch('time.time')
    def test_cancel_execution_with_rollback_no_rollback_step_success(self, patched_time, patched_sleep):
        mock_sleep = MockSleep()
        patched_time.side_effect = mock_sleep.time
        patched_sleep.side_effect = mock_sleep.sleep

        execution_1 = prepare_execution_description(SSM_STEP_NAME, 'InProgress')
        execution_2 = prepare_execution_description(SSM_STEP_NAME, 'Success')
        execution_3 = prepare_execution_description(SSM_STEP_NAME, 'Success')
        self.mock_ssm.get_automation_execution.side_effect = [execution_1, execution_2, execution_3]
        self.ssm_document.cancel_execution_with_rollback('test_execution_id')
        self.mock_ssm.stop_automation_execution.assert_called_once()
        self.mock_ssm.get_automation_execution.assert_has_calls([call(AutomationExecutionId='test_execution_id'),
                                                                 call(AutomationExecutionId='test_execution_id'),
                                                                 call(AutomationExecutionId='test_execution_id')])
        self.assertEqual(self.mock_ssm.get_automation_execution.call_count, 3)

    def test_get_successfully_executed_steps_by_order(self):
        self.mock_ssm.get_automation_execution.return_value = prepare_execution_description_with_multiple_steps()
        steps = self.ssm_document.get_successfully_executed_steps_by_order('test_execution_id')
        self.mock_ssm.get_automation_execution.assert_called_once_with(AutomationExecutionId='test_execution_id')
        self.assertEqual(steps, ['1', '2', '3', '4'])

    # execution_id: str, step_name: str, steps: [] = None
    def test_get_execution_step_url_with_no_passed_execs_success(self):
        execution_id = 'test_execution_1'
        step_name = 'test_step'
        step_id = 'test_step_1'
        execution = {'AutomationExecution':
                     {'StepExecutions': [{'StepStatus': 'InProgress',
                                          'StepName': step_name,
                                          'StepExecutionId': step_id}],
                      'AutomationExecutionStatus': 'InProgress'}}

        self.mock_ssm.get_automation_execution.return_value = execution

        expected_url = f'https://{self.region_name}.console.aws.amazon.com/systems-manager/' \
                       f'automation/execution/{execution_id}/step/1/{step_id}'
        actual_url = self.ssm_document.get_execution_step_url(execution_id, step_name)
        self.assertEqual(expected_url, actual_url)
        self.mock_ssm.get_automation_execution.assert_called_once()

    def test_get_execution_step_url_with_passed_execs_success(self):
        execution_id = 'test_execution_1'
        step_name = 'test_step'
        step_id = 'test_step_1'
        execution = {'AutomationExecution':
                     {'StepExecutions': [{'StepStatus': 'InProgress',
                                          'StepName': step_name,
                                          'StepExecutionId': step_id}],
                      'AutomationExecutionStatus': 'InProgress'}}

        expected_url = f'https://{self.region_name}.console.aws.amazon.com/systems-manager/' \
                       f'automation/execution/{execution_id}/step/1/{step_id}'
        steps = execution['AutomationExecution']['StepExecutions']
        actual_url = self.ssm_document.get_execution_step_url(execution_id, step_name, steps)
        self.assertEqual(expected_url, actual_url)
        self.mock_ssm.get_automation_execution.assert_not_called()

    def test_get_execution_step_url_with_passed_execs_no_step_fail(self):
        execution_id = 'test_execution_1'
        step_name = 'test_step'
        execution = {'AutomationExecution': {'StepExecutions': [],
                                             'AutomationExecutionStatus': 'InProgress'}}
        steps = execution['AutomationExecution']['StepExecutions']
        self.assertRaises(Exception, self.ssm_document.get_execution_step_url, execution_id, step_name, steps)

    def test_get_execution_url_success(self):
        execution_id = 'test_execution_1'
        expected_url = f'https://{self.region_name}.console.aws.amazon.com/systems-manager/' \
                       f'automation/execution/{execution_id}'
        actual_url = self.ssm_document.get_execution_url(execution_id)
        self.assertEqual(expected_url, actual_url)

    def test_parse_input_parameters(self):
        cf_output = {'VPC': {'PublicSubnet2Cidr': '10.0.1.0/24', 'PublicSubnetOne': 'subnet-09681e26eaa5d7619',
                             'List': ['item1'],
                             'VPCId': 'vpc-0a57667ce26318a1e', 'PublicSubnetTwo': 'subnet-0833ad073dc1f378e',
                             'VPCCidr': '10.0.0.0/16', 'PrivateSubnetWithoutInternetOne': 'subnet-0cc8005cb344bc14e',
                             'PrivateSubnetWithoutInternetTwo': 'subnet-048dbf805312acf82',
                             'PublicSubnet1Cidr': '10.0.0.0/24',
                             'PrivateSubnetWithoutInternetThree': 'subnet-0a88466533a0ff0a3'},
                     'SnsForAlarms': {
                         'Topic': 'arn:aws:sns:eu-central-1:435978235099:SnsForAlarms-zzz'}}
        cfn_installed_alarms = {'under_test': {'AlarmName': 'network-unhealthy-host-count-B2e6-0'}}
        cache = {"SsmExecutionId": {"1": 'id1'}}
        input_parameters = """\
|cf_output|alarm_input|cache_input|list|
|{{cfn-output:VPC>PublicSubnetOne}}|{{alarm:under_test>AlarmName}}|{{cache:SsmExecutionId>1}}|{{cfn-output:VPC>List}}"""
        res = self.ssm_document.parse_input_parameters(cf_output, cfn_installed_alarms, cache, input_parameters)
        self.assertEqual(res,
                         {'cf_output': ['subnet-09681e26eaa5d7619'],
                          'alarm_input': ['network-unhealthy-host-count-B2e6-0'],
                          'cache_input': ['id1'],
                          'list': ['item1']})

    def test_send_resume_signal(self):
        self.mock_ssm.send_automation_signal.return_value = {}
        self.ssm_document.send_resume_signal('dummy_execution', 'step1')
        self.mock_ssm.send_automation_signal.assert_called_once()
