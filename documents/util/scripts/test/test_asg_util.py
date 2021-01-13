import unittest
import pytest
from unittest.mock import patch
from unittest.mock import MagicMock
from test import test_data_provider
from src.asg_util import get_instance_ids_by_percentage, get_instance_ids_in_asg_random_az
from src.asg_util import start_instance_refresh, cancel_instance_refresh, assert_no_refresh_in_progress
from src.asg_util import wait_for_refresh_to_finish, assert_no_suspended_process, get_instance_ids_in_asg
from src.asg_util import get_networking_configuration_from_asg, suspend_launch


@pytest.mark.unit_test
class TestAsgUtil(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('boto3.client')
        self.client = self.patcher.start()
        self.mock_autoscaling = MagicMock()
        self.side_effect_map = {
            'autoscaling': self.mock_autoscaling
        }
        self.client.side_effect = lambda service_name: self.side_effect_map.get(service_name)
        self.mock_autoscaling.describe_auto_scaling_groups.return_value = \
            test_data_provider.get_sample_describe_auto_scaling_groups_response()
        self.mock_autoscaling.describe_launch_configurations.return_value = \
            test_data_provider.get_sample_describe_launch_configurations_response()

    def tearDown(self):
        self.patcher.stop()

    def test_get_instance_ids_in_asg(self):
        events = {}
        events['AutoScalingGroupName'] = test_data_provider.ASG_NAME

        output = get_instance_ids_in_asg(events, None)
        self.assertEqual([test_data_provider.INSTANCE_ID], output['InstanceIds'])

    def test_get_instance_ids_in_asg_random_az(self):
        events = {}
        events['AutoScalingGroupName'] = test_data_provider.ASG_NAME

        output = get_instance_ids_in_asg_random_az(events, None)
        self.assertEqual([test_data_provider.INSTANCE_ID], output['InstanceIds'])

    def test_get_networking_configuration_from_asg(self):
        events = {}
        events['AutoScalingGroupName'] = test_data_provider.ASG_NAME

        output = get_networking_configuration_from_asg(events, None)
        self.assertEqual(test_data_provider.SUBNET_GROUPS.split(','), output['SubnetIds'])
        self.assertEqual(test_data_provider.SECURITY_GROUP, output['SecurityGroup'])

    def test_suspend_launch(self):
        events = {}
        events['AutoScalingGroupName'] = test_data_provider.ASG_NAME

        suspend_launch(events, None)
        self.mock_autoscaling.suspend_processes.assert_called_once()

    def test_start_instance_refresh(self):
        events = {}
        events['AutoScalingGroupName'] = test_data_provider.ASG_NAME
        events['PercentageOfInstances'] = 20

        start_instance_refresh(events, None)
        self.mock_autoscaling.start_instance_refresh.assert_called_once()

    def test_cancel_instance_refresh(self):
        events = {}
        events['AutoScalingGroupName'] = test_data_provider.ASG_NAME

        cancel_instance_refresh(events, None)
        self.mock_autoscaling.cancel_instance_refresh.assert_called_once()

    def test_wait_for_refresh_to_finish_success(self):
        events = {}
        events['AutoScalingGroupName'] = test_data_provider.ASG_NAME
        events['InstanceRefreshId'] = test_data_provider.INSTANCE_REFRESH_ID

        self.mock_autoscaling.describe_instance_refreshes.return_value = \
            test_data_provider.get_sample_describe_instance_refreshes_response('Successful')
        wait_for_refresh_to_finish(events, None)
        self.mock_autoscaling.describe_instance_refreshes.assert_called_once()

    def test_wait_for_refresh_to_finish_cancelled(self):
        events = {}
        events['AutoScalingGroupName'] = test_data_provider.ASG_NAME
        events['InstanceRefreshId'] = test_data_provider.INSTANCE_REFRESH_ID

        self.mock_autoscaling.describe_instance_refreshes.return_value = \
            test_data_provider.get_sample_describe_instance_refreshes_response('Cancelled')
        self.assertRaises(Exception, wait_for_refresh_to_finish, events, None)

    def test_assert_no_refresh_in_progress_success(self):
        events = {}
        events['AutoScalingGroupName'] = test_data_provider.ASG_NAME

        assert_no_refresh_in_progress(events, None)
        self.mock_autoscaling.describe_instance_refreshes.assert_called_once()

    def test_assert_no_refresh_in_progress_fail(self):
        events = {}
        events['AutoScalingGroupName'] = test_data_provider.ASG_NAME

        self.mock_autoscaling.describe_instance_refreshes.return_value = \
            test_data_provider.get_sample_describe_instance_refreshes_response('Pending')
        self.assertRaises(Exception, assert_no_refresh_in_progress, events, None)

    def test_assert_no_suspended_process_success(self):
        events = {}
        events['AutoScalingGroupName'] = test_data_provider.ASG_NAME

        assert_no_suspended_process(events, None)
        self.mock_autoscaling.describe_auto_scaling_groups.assert_called_once()

    def test_assert_no_suspended_process_fail(self):
        events = {}
        events['AutoScalingGroupName'] = test_data_provider.ASG_NAME

        self.mock_autoscaling.describe_auto_scaling_groups.return_value = test_data_provider\
            .get_sample_describe_auto_scaling_groups_response_with_suspended_processes()

        self.assertRaises(Exception, assert_no_suspended_process, events, None)

    def test_get_instances_by_percentage_50_percent_success(self):
        events = {}
        events['InstanceIds'] = test_data_provider.get_instance_ids_by_count(10)
        events['Percentage'] = 50
        output = get_instance_ids_by_percentage(events, None)

        self.assertEqual(len(output['InstanceIds']), 5)

    def test_get_instances_by_percentage_1_percent_success(self):
        events = {}
        events['InstanceIds'] = test_data_provider.get_instance_ids_by_count(10)
        events['Percentage'] = 1
        output = get_instance_ids_by_percentage(events, None)

        self.assertEqual(len(output['InstanceIds']), 1)

    def test_get_instances_by_percentage_100_percent_success(self):
        events = {}
        events['InstanceIds'] = test_data_provider.get_instance_ids_by_count(10)
        events['Percentage'] = 100
        output = get_instance_ids_by_percentage(events, None)

        self.assertEqual(len(output['InstanceIds']), 10)

    def test_get_instances_by_percentage_0_percent_fail(self):
        events = {}
        events['InstanceIds'] = test_data_provider.get_instance_ids_by_count(10)
        events['Percentage'] = 0
        self.assertRaises(Exception, get_instance_ids_by_percentage, events, None)

    def test_get_instances_by_percentage_0_instances_fail(self):
        events = {}
        events['InstanceIds'] = test_data_provider.get_instance_ids_by_count(0)
        events['Percentage'] = 10
        self.assertRaises(Exception, get_instance_ids_by_percentage, events, None)

    def test_get_instances_by_percentage_negative_percent_fail(self):
        events = {}
        events['InstanceIds'] = test_data_provider.get_instance_ids_by_count(10)
        events['Percentage'] = -10
        self.assertRaises(Exception, get_instance_ids_by_percentage, events, None)
