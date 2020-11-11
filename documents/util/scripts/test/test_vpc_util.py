import unittest
import pytest
from unittest.mock import patch
from unittest.mock import MagicMock
from test import test_data_provider
from src.vpc_util import get_public_subnet_in_private_subnet_vpc


@pytest.mark.unit_test
class TestVpcUtil(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('boto3.client')
        self.client = self.patcher.start()
        self.mock_ec2 = MagicMock()
        self.side_effect_map = {
            'ec2': self.mock_ec2
        }
        self.client.side_effect = lambda service_name: self.side_effect_map.get(service_name)
        self.mock_ec2.describe_subnets.return_value = test_data_provider.get_sample_describe_subnets_response()
        self.mock_ec2.describe_route_tables.return_value = test_data_provider.get_sample_route_table_response()

    def tearDown(self):
        self.patcher.stop()

    def test_get_public_subnet_in_private_subnet_vpc(self):
        events = {}
        events['SubnetIds'] = test_data_provider.APPLICATION_SUBNET_ID

        output = get_public_subnet_in_private_subnet_vpc(events, None)
        self.assertEqual(test_data_provider.PUBLIC_SUBNET_ID, output['PublicSubnetId'])