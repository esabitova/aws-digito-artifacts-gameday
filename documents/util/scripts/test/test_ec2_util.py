import unittest
import pytest
from unittest.mock import patch
from unittest.mock import MagicMock
from test import test_data_provider
from src.ec2_util import get_bigger_instance


@pytest.mark.unit_test
class TestEc2Util(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('boto3.client')
        self.client = self.patcher.start()
        self.mock_ec2 = MagicMock()
        self.side_effect_map = {
            'ec2': self.mock_ec2
        }
        self.client.side_effect = lambda service_name, config=None: self.side_effect_map.get(service_name)
        self.mock_ec2.describe_instance_type_offerings.return_value = \
            test_data_provider.get_sample_describe_instance_type_offerings_response()

    def tearDown(self):
        self.patcher.stop()

    def test_get_bigger_instance_success(self):
        events = {'CurrentInstanceType': test_data_provider.SMALLER_INSTANCE, 'RequestInstanceType': None}
        result = get_bigger_instance(events, None)
        self.assertEqual(result['TargetInstanceType'], test_data_provider.BIGGER_INSTANCE)

    def test_get_bigger_instance_with_request_success(self):
        events = {'RequestInstanceType': test_data_provider.SMALLER_INSTANCE}
        result = get_bigger_instance(events, None)
        self.assertEqual(result['TargetInstanceType'], test_data_provider.SMALLER_INSTANCE)

    def test_get_bigger_instance_fail(self):
        events = {'RequestInstanceType': "Invalid Instance Type"}
        self.mock_ec2.describe_instance_type_offerings.return_value = None
        with pytest.raises(Exception) as key_error:
            get_bigger_instance(events, None)
        assert 'Requested instance type is not valid: Invalid Instance Type' in str(key_error.value)
