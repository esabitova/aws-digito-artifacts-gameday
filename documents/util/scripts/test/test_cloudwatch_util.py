import unittest
import time
import pytest
from src.cloudwatch_util import describe_metric_alarm_state, get_ec2_metric_max_datapoint, verify_ec2_stress
from unittest.mock import patch
from unittest.mock import MagicMock
from test.test_data_provider import get_instance_ids_by_count


@pytest.mark.unit_test
class TestCloudWatchUtil(unittest.TestCase):

    def setUp(self):
        self.patcher = patch('boto3.client')
        self.client = self.patcher.start()
        self.cw_mock = MagicMock()
        self.side_effect_map = {
            'cloudwatch': self.cw_mock
        }
        self.client.side_effect = lambda service_name: self.side_effect_map.get(service_name)

    def tearDown(self):
        self.patcher.stop()

    def test_verify_ec2_stress_low_cpu_failed(self):
        expected_cpu_load = 95
        actual_cpu_load = '50'
        self.cw_mock.get_metric_statistics.return_value = {'Datapoints': [{'Maximum': actual_cpu_load},
                                                                          {'Maximum': '3'},
                                                                          {'Maximum': '8'}]}

        stress_duration = 3
        exp_recovery_time = 10
        instance_ids = get_instance_ids_by_count(5)
        metric_delay_secs = 5
        self.assertRaises(Exception, verify_ec2_stress, instance_ids,
                          stress_duration, expected_cpu_load, metric_delay_secs, 'CPUUtilization', exp_recovery_time)

    def test_verify_ec2_stress_metric_wait_time_10_success(self):
        expected_cpu_load = 95
        actual_cpu_load = '95'
        self.cw_mock.get_metric_statistics.return_value = {'Datapoints': [{'Maximum': actual_cpu_load},
                                                                          {'Maximum': '3'},
                                                                          {'Maximum': '8'}]}
        stress_duration = 3
        exp_recovery_time = 10
        instance_ids = get_instance_ids_by_count(5)
        metric_delay_secs = 5

        start_time = time.time()
        verify_ec2_stress(instance_ids, stress_duration, expected_cpu_load, metric_delay_secs, 'CPUUtilization',
                          exp_recovery_time)
        end_time = time.time()
        self.assertEqual(round(end_time - start_time), 0)

    def test_verify_ec2_stress_metric_wait_time_1_success(self):
        expected_cpu_load = 95
        actual_cpu_load = '95'
        self.cw_mock.get_metric_statistics.return_value = {'Datapoints': [{'Maximum': actual_cpu_load},
                                                                          {'Maximum': '3'}, {'Maximum': '8'}]}

        stress_duration = 3
        exp_recovery_time = 1
        instance_ids = get_instance_ids_by_count(5)
        metric_delay_secs = 6

        start_time = time.time()
        verify_ec2_stress(instance_ids, stress_duration, expected_cpu_load, metric_delay_secs, 'CPUUtilization',
                          exp_recovery_time)
        end_time = time.time()
        self.assertEqual(round(end_time - start_time), 2)

    def test_describe_metric_alarm_state_ok_success(self):
        self.cw_mock.describe_alarms.return_value = {'MetricAlarms': [{'StateValue': 'OK'}]}
        state = describe_metric_alarm_state('TestAlarm-1')
        self.assertEqual(state, "OK")

    def test_describe_metric_alarm_state_alarm_success(self):
        self.cw_mock.describe_alarms.return_value = {'MetricAlarms': [{'StateValue': 'Alarm'}]}
        state = describe_metric_alarm_state('TestAlarm-1')
        self.assertEqual(state, 'Alarm')

    def test_describe_metric_alarm_state_alarm_fail(self):
        self.cw_mock.describe_alarms.return_value = {}
        self.assertRaises(Exception, describe_metric_alarm_state, 'TestAlarm-1')

    def test_get_ec2_cpu_metric_max_datapoint_success(self):
        self.cw_mock.get_metric_statistics.return_value = {'Datapoints': [{'Maximum': '10'},
                                                                          {'Maximum': '5'},
                                                                          {'Maximum': '100'},
                                                                          {'Maximum': '7'}]}
        dp = get_ec2_metric_max_datapoint('ec2-instance-1', 'CPUUtilization', None, None)
        self.assertEqual(dp, 100)

    def test_get_ec2_cpu_metric_max_datapoint_no_point(self):
        self.cw_mock.get_metric_statistics.return_value = {'Datapoints': []}
        dp = get_ec2_metric_max_datapoint('ec2-instance-1', 'CPUUtilization', None, None)
        self.assertEqual(dp, 0.0)
