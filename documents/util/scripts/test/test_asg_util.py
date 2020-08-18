import unittest
from unittest.mock import patch
from unittest.mock import MagicMock
from test import test_data_provider

from src.asg_util import get_instance_ids_in_asg,get_networking_configuration_from_asg

class TestAsgUtil(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('boto3.client')
        self.client = self.patcher.start()
        self.mock_autoscaling = MagicMock()
        self.side_effect_map = {
            'autoscaling': self.mock_autoscaling
        }
        self.client.side_effect = lambda service_name: self.side_effect_map.get(service_name)
        self.mock_autoscaling.describe_auto_scaling_groups.return_value = test_data_provider.get_sample_describe_auto_scaling_groups_response()
        self.mock_autoscaling.describe_launch_configurations.return_value = test_data_provider.get_sample_describe_launch_configurations_response()

    def tearDown(self):
        self.patcher.stop()

    def test_get_instance_ids_in_asg(self):
        events = {}
        events['AutoScalingGroupName'] = test_data_provider.ASG_NAME

        output = get_instance_ids_in_asg(events, None)
        self.assertEqual([test_data_provider.INSTANCE_ID], output['InstanceIds'])

    def test_get_networking_configuration_from_asg(self):
        events = {}
        events['AutoScalingGroupName'] = test_data_provider.ASG_NAME

        output = get_networking_configuration_from_asg(events, None)
        self.assertEqual(test_data_provider.SUBNET_GROUPS.split(','), output['SubnetIds'])
        self.assertEqual(test_data_provider.SECURITY_GROUP, output['SecurityGroup'])