import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from documents.util.scripts.src.ssm_execution_util import get_output_from_ssm_step_execution, get_step_durations, \
    get_inputs_from_ssm_execution
from documents.util.scripts.test import test_data_provider


@pytest.mark.unit_test
class TestSsmExecutionUtil(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('boto3.client')
        self.client = self.patcher.start()
        self.mock_ssm = MagicMock()
        self.side_effect_map = {
            'ssm': self.mock_ssm
        }
        self.client.side_effect = lambda service_name: self.side_effect_map.get(service_name)
        self.mock_ssm.get_automation_execution.return_value = test_data_provider.get_sample_ssm_execution_response()

    def tearDown(self):
        self.patcher.stop()

    def test_get_output_from_ssm_step_execution_success(self):
        events = {}
        events['ExecutionId'] = test_data_provider.AUTOMATION_EXECUTION_ID
        events['StepName'] = test_data_provider.STEP_NAME
        events['ResponseField'] = test_data_provider.RESPONSE_FIELD_1 + ',' + test_data_provider.RESPONSE_FIELD_2

        ssm_output = get_output_from_ssm_step_execution(events, None)
        self.assertEqual(test_data_provider.SUCCESS_STATUS, ssm_output[test_data_provider.RESPONSE_FIELD_1])
        self.assertEqual(test_data_provider.INSTANCE_ID, ssm_output[test_data_provider.RESPONSE_FIELD_2])

    def test_get_output_from_ssm_step_execution_fail_missing_input(self):
        events = {}
        self.assertRaises(KeyError, get_output_from_ssm_step_execution, events, None)

    def test_get_output_from_ssm_step_execution_fail_missing_step_name(self):
        events = {}
        events['ExecutionId'] = test_data_provider.AUTOMATION_EXECUTION_ID
        events['StepName'] = test_data_provider.MISSING_STEP_NAME
        events['ResponseField'] = test_data_provider.RESPONSE_FIELD_1 + ',' + test_data_provider.RESPONSE_FIELD_2

        self.assertRaises(Exception, get_output_from_ssm_step_execution, events, None)

    def test_get_step_durations(self):
        events = {}
        events['ExecutionId'] = test_data_provider.AUTOMATION_EXECUTION_ID
        events['StepName'] = test_data_provider.STEP_NAME

        duration = get_step_durations(events, None)
        self.assertEqual(str(test_data_provider.STEP_DURATION), duration['duration'])

    def test_get_step_durations_fail_missing_input(self):
        events = {}

        self.assertRaises(KeyError, get_step_durations, events, None)

    def test_get_step_durations_fail_missing_step_name(self):
        events = {}
        events['ExecutionId'] = test_data_provider.AUTOMATION_EXECUTION_ID
        events['StepName'] = test_data_provider.MISSING_STEP_NAME

        self.assertRaises(Exception, get_step_durations, events, None)

    def test_get_inputs_from_ssm_execution_empty_events(self):
        events = {}
        self.assertRaises(KeyError, get_inputs_from_ssm_execution, events, None)

    def test_get_inputs_from_ssm_execution_empty_input_fields(self):
        events = {
            'ExecutionId': test_data_provider.AUTOMATION_EXECUTION_ID
        }
        self.assertRaises(KeyError, get_inputs_from_ssm_execution, events, None)

    def test_get_inputs_from_ssm_execution_empty_input_fields_execution_id(self):
        events = {
            'InputFields': 'some-data'
        }
        self.assertRaises(KeyError, get_inputs_from_ssm_execution, events, None)

    def test_get_inputs_from_ssm_execution(self):
        events = {
            'ExecutionId': test_data_provider.AUTOMATION_EXECUTION_ID,
            'InputFields': f'{test_data_provider.SSM_EXECUTION_PARAMETER_1}, '
                           f'{test_data_provider.SSM_EXECUTION_PARAMETER_2},'
                           f'{test_data_provider.SSM_EXECUTION_PARAMETER_3}'
        }
        actual_output = get_inputs_from_ssm_execution(events, None)
        self.assertEqual(test_data_provider.SSM_EXECUTION_PARAMETER_1_VALUE,
                         actual_output[test_data_provider.SSM_EXECUTION_PARAMETER_1])
        self.assertEqual(test_data_provider.SSM_EXECUTION_PARAMETER_2_VALUE,
                         actual_output[test_data_provider.SSM_EXECUTION_PARAMETER_2])
        self.assertEqual(test_data_provider.SSM_EXECUTION_PARAMETER_3_VALUE,
                         actual_output[test_data_provider.SSM_EXECUTION_PARAMETER_3])

    def test_get_inputs_from_ssm_execution_input_fields_non_existing(self):
        events = {
            'ExecutionId': test_data_provider.AUTOMATION_EXECUTION_ID,
            'InputFields': 'blabla'
        }
        self.assertRaises(KeyError, get_inputs_from_ssm_execution, events, None)
