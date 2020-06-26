import unittest
from test import test_data_provider
from unittest.mock import patch
from unittest.mock import MagicMock

from src.ssm_execution_util import get_output_from_ssm_step_execution

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
        events['StepName'] =  test_data_provider.STEP_NAME
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
