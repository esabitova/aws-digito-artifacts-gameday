import unittest
import pytest
from unittest.mock import patch
from unittest.mock import MagicMock
from test import test_data_provider

from src.ami_util import get_ami_id

@pytest.mark.unit_test
class TestAmiUtil(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('boto3.client')
        self.client = self.patcher.start()
        self.mock_ec2 = MagicMock()
        self.side_effect_map = {
            'ec2': self.mock_ec2
        }
        self.client.side_effect = lambda service_name: self.side_effect_map.get(service_name)
        self.mock_ec2.describe_images.return_value = test_data_provider.get_sample_describe_images_response()

    def tearDown(self):
        self.patcher.stop()

    def test_get_ami_id(self):
        events = {}
        events['AmiName'] = test_data_provider.AMI_NAME

        ami_output = get_ami_id(events, None)
        self.assertEqual(test_data_provider.AMI_ID, ami_output['AmiId'])