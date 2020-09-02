import unittest
from unittest.mock import patch
from unittest.mock import MagicMock
from test import test_data_provider

from src.security_group_util import allow_access_to_self

class TestSecurityGroupUtil(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('boto3.client')
        self.client = self.patcher.start()
        self.mock_ec2 = MagicMock()
        self.side_effect_map = {
            'ec2': self.mock_ec2
        }
        self.client.side_effect = lambda service_name: self.side_effect_map.get(service_name)
        self.mock_ec2.describe_security_groups.return_value = test_data_provider.get_sample_describe_security_groups_response()
        self.mock_ec2.authorize_security_group_ingress.return_value = {}

    def tearDown(self):
        self.patcher.stop()

    def test_allow_access_to_self_rule_exists(self):
        events = {}
        events['AccountId'] = test_data_provider.ACCOUNT_ID
        events['SecurityGroupId'] = test_data_provider.SECURITY_GROUP

        allow_access_to_self(events, None)

    def test_allow_access_to_self_rule_does_not_exist(self):
        events = {}
        events['AccountId'] = test_data_provider.ACCOUNT_ID
        events['SecurityGroupId'] = 'non_existing_sg'

        allow_access_to_self(events, None)