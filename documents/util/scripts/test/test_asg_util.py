import unittest
import pytest
from unittest.mock import patch
from unittest.mock import MagicMock
from test import test_data_provider
from src.asg_util import get_instance_ids_by_percentage, get_instance_ids_in_asg_random_az
from src.asg_util import start_instance_refresh, cancel_instance_refresh, assert_no_refresh_in_progress
from src.asg_util import wait_for_refresh_to_finish, assert_no_suspended_process, get_instance_ids_in_asg
from src.asg_util import get_networking_configuration_from_asg, suspend_launch, wait_for_in_service
from src.asg_util import get_instance_data, update_asg, rollback_scaleup


@pytest.mark.unit_test
class TestAsgUtil(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('boto3.client')
        self.client = self.patcher.start()
        self.mock_autoscaling = MagicMock()
        self.mock_ec2 = MagicMock()
        self.side_effect_map = {
            'autoscaling': self.mock_autoscaling,
            'ec2': self.mock_ec2
        }
        self.client.side_effect = lambda service_name, config=None: self.side_effect_map.get(service_name)
        self.mock_autoscaling.describe_auto_scaling_groups.return_value = \
            test_data_provider.get_sample_describe_auto_scaling_groups_response()
        self.mock_autoscaling.describe_launch_configurations.return_value = \
            test_data_provider.get_sample_describe_launch_configurations_response()
        self.mock_ec2.describe_launch_template_versions.return_value = \
            test_data_provider.get_sample_describe_launch_template_versions_response()
        self.mock_ec2.describe_instance_type_offerings.return_value = \
            test_data_provider.get_sample_describe_instance_type_offerings_response()
        self.mock_ec2.create_launch_template_version.return_value = \
            test_data_provider.get_sample_create_launch_template_version_response()

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

    def test_wait_for_in_service_returns_if_ready(self):
        events = {'AutoScalingGroupName': test_data_provider.ASG_NAME, 'NewDesiredCapacity': 1}
        wait_for_in_service(events, None)
        self.mock_autoscaling.describe_auto_scaling_groups.assert_called_once()

    @patch('time.sleep', return_value=None)
    def test_wait_for_in_service_waits_until_ready(self, patched_time_sleep):
        events = {'AutoScalingGroupName': test_data_provider.ASG_NAME, 'NewDesiredCapacity': 1}
        self.mock_autoscaling.describe_auto_scaling_groups.side_effect = \
            [test_data_provider.get_sample_describe_auto_scaling_groups_response(lifecycle_state='Pending'),
             test_data_provider.get_sample_describe_auto_scaling_groups_response(lifecycle_state='InService')]
        wait_for_in_service(events, None)
        self.assertEqual(self.mock_autoscaling.describe_auto_scaling_groups.call_count, 2)
        patched_time_sleep.assert_called_once()

    def test_get_instance_data_launch_config_success(self):
        events = {'AutoScalingGroupName': test_data_provider.ASG_NAME}
        instance_data = get_instance_data(events, None)
        self.assertEqual(instance_data['OriginalInstanceType'], test_data_provider.SMALLER_INSTANCE)
        self.assertEqual(instance_data['BiggerInstanceType'], test_data_provider.BIGGER_INSTANCE)
        self.assertEqual(instance_data['LaunchTemplateName'], '')
        self.assertEqual(instance_data['LaunchTemplateVersion'], '')

    def test_get_instance_data_launch_template_success(self):
        events = {'AutoScalingGroupName': test_data_provider.ASG_NAME}
        self.mock_autoscaling.describe_auto_scaling_groups.return_value = \
            test_data_provider.get_sample_describe_asg_w_launch_template_response()
        instance_data = get_instance_data(events, None)
        self.assertEqual(instance_data['OriginalInstanceType'], test_data_provider.SMALLER_INSTANCE)
        self.assertEqual(instance_data['BiggerInstanceType'], test_data_provider.BIGGER_INSTANCE)
        self.assertEqual(instance_data['LaunchTemplateName'], 'MyLaunchTemp')
        self.assertEqual(instance_data['LaunchTemplateVersion'], 4)

    def test_get_instance_data_mixed_instances_policy_fail(self):
        events = {'AutoScalingGroupName': test_data_provider.ASG_NAME}
        self.mock_autoscaling.describe_auto_scaling_groups.return_value = \
            test_data_provider.get_sample_describe_auto_scaling_groups_response(mixed_instances_policy=True)
        self.assertRaises(Exception, get_instance_data, events, None)

    def test_update_asg_launch_template_success(self):
        events = {'AutoScalingGroupName': test_data_provider.ASG_NAME,
                  'BiggerInstanceType': test_data_provider.BIGGER_INSTANCE,
                  'LaunchTemplateName': 'MyLaunchTemp',
                  'LaunchTemplateVersion': '4'}
        self.mock_autoscaling.describe_auto_scaling_groups.return_value = \
            test_data_provider.get_sample_describe_asg_w_launch_template_response()
        update_asg(events, None)
        new_launch_template = {'LaunchTemplateName': 'MyLaunchTemp', 'Version': '5'}
        self.mock_autoscaling.update_auto_scaling_group.assert_called_with(
            AutoScalingGroupName=test_data_provider.ASG_NAME, LaunchTemplate=new_launch_template)

    def test_update_asg_launch_config_success(self):
        events = {'AutoScalingGroupName': test_data_provider.ASG_NAME,
                  'BiggerInstanceType': test_data_provider.BIGGER_INSTANCE,
                  'LaunchTemplateName': '',
                  'LaunchTemplateVersion': ''}
        updated_asg = update_asg(events, None)
        launch_config_name = updated_asg['LaunchConfigOrTemplate']
        self.mock_autoscaling.create_launch_configuration.assert_called_with(
            InstanceType=test_data_provider.BIGGER_INSTANCE,
            SecurityGroups=[test_data_provider.SECURITY_GROUP],
            LaunchConfigurationName=launch_config_name)
        self.mock_autoscaling.update_auto_scaling_group.assert_called_with(
            AutoScalingGroupName=test_data_provider.ASG_NAME, LaunchConfigurationName=launch_config_name)

    def test_rollback_scaleup_launch_template_success(self):
        events = {'AutoScalingGroupName': test_data_provider.ASG_NAME,
                  'LaunchTemplateName': 'MyLaunchTemp',
                  'LaunchTemplateVersion': '4',
                  'LaunchConfigOrTemplate': 'MyLaunchTemp:5'}
        rollback_scaleup(events, None)
        self.mock_autoscaling.update_auto_scaling_group.assert_called_with(
            AutoScalingGroupName=test_data_provider.ASG_NAME,
            LaunchTemplate={'LaunchTemplateName': 'MyLaunchTemp', 'Version': '4'})
        self.mock_ec2.delete_launch_template_versions.assert_called_with(
            LaunchTemplateName='MyLaunchTemp', Versions=['5'])

    def test_rollback_scaleup_launch_config_success(self):
        events = {'AutoScalingGroupName': test_data_provider.ASG_NAME,
                  'LaunchTemplateName': '',
                  'LaunchTemplateVersion': '',
                  'LaunchConfigurationName': 'OriginalLaunchConfig',
                  'LaunchConfigOrTemplate': 'NewLaunchConfig'}
        rollback_scaleup(events, None)
        self.mock_autoscaling.update_auto_scaling_group.assert_called_with(
            AutoScalingGroupName=test_data_provider.ASG_NAME, LaunchConfigurationName='OriginalLaunchConfig')
        self.mock_autoscaling.delete_launch_configuration.assert_called_with(LaunchConfigurationName='NewLaunchConfig')
