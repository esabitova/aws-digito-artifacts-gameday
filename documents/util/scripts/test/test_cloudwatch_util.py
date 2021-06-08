import datetime
import time
import unittest
from unittest.mock import MagicMock, call, patch
from parameterized import parameterized

import pytest
from documents.util.scripts.src.cloudwatch_util import (
    _describe_metric_alarms, _execute_boto3_cloudwatch, _execute_boto3_cloudwatch_paginator, _put_metric_alarm,
    copy_alarms_for_dynamo_db_table, describe_metric_alarm_state,
    get_ec2_metric_max_datapoint, get_metric_alarm_threshold_values,
    verify_alarm_triggered, verify_ec2_stress)
from documents.util.scripts.test.test_data_provider import \
    get_instance_ids_by_count

GENERIC_SUCCESS_RESULT = {
    "ResponseMetadata": {
        "HTTPStatusCode": 200
    }
}
DESCRIBE_ALARMS_RESPONSE = {
    **GENERIC_SUCCESS_RESULT,
    "MetricAlarms": [
        {
            "AlarmName": "TargetTracking-table/myable-AlarmHigh-2b8fb5f6-8477-4904-9ffb-cb4112e71b3c",
            "AlarmArn": "arn:aws:cloudwatch:us-east-2:435978235099:alarm:'\
            'TargetTracking-table/myable-AlarmHigh-2b8fb5f6-8477-4904-9ffb-cb4112e71b3c",
            "AlarmDescription": "descr",
            "AlarmConfigurationUpdatedTimestamp": "2021-04-08T14:25:05.077000+00:00",
            "ActionsEnabled": True,
            "OKActions": [],
            "AlarmActions": [
                "arn:aws:autoscaling:us-east-2:435978235099:scalingPolicy:61dedb74-0a54-422a-8a67-2b84c1adec92:'\
                    'resource/dynamodb/table/myable:policyName/DynamoDBWriteCapacityUtilization:'\
                        'table/myable:createdBy/9f25e21a-8186-4832-8f16-51777da24a1a"
            ],
            "InsufficientDataActions": [],
            "StateValue": "OK",
            "StateReason": "Some Reason",
            "StateReasonData": "Some data",
            "StateUpdatedTimestamp": "2021-04-08T14:29:26.001000+00:00",
            "MetricName": "ConsumedWriteCapacityUnits",
            "Namespace": "AWS/DynamoDB",
            "Statistic": "Sum",
            "Dimensions": [
                {
                    "Name": "TableName",
                    "Value": "source_table"
                }
            ],
            "Period": 60,
            "EvaluationPeriods": 2,
            "Threshold": 210.0,
            "ComparisonOperator": "GreaterThanThreshold"
        }
    ]
}


@pytest.mark.unit_test
class TestCloudWatchUtil(unittest.TestCase):

    def setUp(self):
        self.patcher = patch('boto3.client')
        self.client = self.patcher.start()
        self.cw_mock = MagicMock()
        self.side_effect_map = {
            'cloudwatch': self.cw_mock
        }
        self.client.side_effect = lambda service_name, config=None: self.side_effect_map.get(service_name)
        self.cw_mock.describe_alarms.return_value = \
            DESCRIBE_ALARMS_RESPONSE
        self.cw_mock.put_metric_alarm.return_value = \
            GENERIC_SUCCESS_RESULT

    def tearDown(self):
        self.patcher.stop()

    def test__execute_boto3_cloudwatch(self):
        with self.assertRaises(ValueError):
            _execute_boto3_cloudwatch(lambda x: {'ResponseMetadata': {'HTTPStatusCode': 500}})

    def test__execute_boto3_cloudwatch_paginator(self):
        paginator_mock = MagicMock()
        self.cw_mock.get_paginator.return_value = paginator_mock

        paginate_mock = MagicMock()
        paginator_mock.paginate.return_value = paginate_mock
        paginate_mock.search.return_value = iter(['some value'])

        _execute_boto3_cloudwatch_paginator(func_name='my_func', search_exp='Collection[]', value1='abc')
        self.cw_mock.get_paginator.assert_called_with('my_func')
        paginator_mock.paginate.assert_called_with(value1='abc')
        paginate_mock.search.assert_called_with('Collection[]')

    def test__execute_boto3_auto_cloudwatch__page_iterator(self):
        paginator_mock = MagicMock()
        self.cw_mock.get_paginator.return_value = paginator_mock

        paginate_mock = MagicMock()
        paginator_mock.paginate.return_value = paginate_mock
        paginate_mock.search.return_value = iter(['some value'])

        _execute_boto3_cloudwatch_paginator(func_name='my_func', value1='abc')
        self.cw_mock.get_paginator.assert_called_with('my_func')
        paginator_mock.paginate.assert_called_with(value1='abc')
        paginate_mock.search.assert_not_called()

    @patch('documents.util.scripts.src.cloudwatch_util._execute_boto3_cloudwatch_paginator',
           return_value=iter([{'AlarmName': '1'}]))
    def test__describe_metric_alarms(self, paginator_mock):

        result = _describe_metric_alarms(alarm_names=['alarm_name1'])

        self.assertEqual(list(result), [{'AlarmName': '1'}])
        paginator_mock.assert_has_calls([call(func_name='describe_alarms',
                                              search_exp='MetricAlarms[]',
                                              AlarmTypes=['MetricAlarm'],
                                              AlarmNames=['alarm_name1'])])

    def test__put_metric_alarm(self):

        result = _put_metric_alarm(AlarmName='ABC')

        self.assertEqual(result, GENERIC_SUCCESS_RESULT)

    @parameterized.expand([
        ({}, {}),
        ({'SourceTableName': 'my_table'}, {}),
        ({'SourceTableName': 'my_table', 'TargetTableName': 'target_table'}, {})
    ])
    def test_copy_alarms_for_dynamo_db_table_raises_exception(self, events, context):
        with self.assertRaises(KeyError):
            copy_alarms_for_dynamo_db_table(events=events, context=context)

    @patch('documents.util.scripts.src.cloudwatch_util._describe_metric_alarms',
           return_value=iter(DESCRIBE_ALARMS_RESPONSE['MetricAlarms']))
    @patch('documents.util.scripts.src.cloudwatch_util._put_metric_alarm',
           return_value=DESCRIBE_ALARMS_RESPONSE)
    def test_copy_alarms_for_dynamo_db_table(self, describe_mock, put_mock):

        result = copy_alarms_for_dynamo_db_table(events={
            'SourceTableName': 'source_table',
            'TargetTableName': 'target_table',
            'DynamoDBSourceTableAlarmNames':
            ['TargetTracking-table/myable-AlarmHigh-2b8fb5f6-8477-4904-9ffb-cb4112e71b3c']
        }, context={})

        self.assertEqual(result['AlarmsChanged'], 1)
        describe_mock.assert_called()
        put_mock.assert_called()

    def test_verify_ec2_stress_low_cpu_failed(self):
        expected_cpu_load = 95
        actual_cpu_load = '50'
        latest_timestamp = datetime.datetime.utcnow() + datetime.timedelta(seconds=200)
        self.cw_mock.get_metric_statistics.return_value = {
            'Datapoints': [
                {'Maximum': actual_cpu_load, 'Timestamp': latest_timestamp},
                {'Maximum': '3', 'Timestamp': datetime.datetime.utcnow()},
                {'Maximum': '8', 'Timestamp': datetime.datetime.utcnow()}
            ]
        }

        stress_duration = 3
        exp_recovery_time = 10
        instance_ids = get_instance_ids_by_count(5)
        metric_delay_secs = 5
        self.assertRaises(Exception, verify_ec2_stress, instance_ids,
                          stress_duration, expected_cpu_load, metric_delay_secs, 'CPUUtilization', exp_recovery_time)

    def test_verify_ec2_stress_metric_wait_time_10_success(self):
        expected_cpu_load = 95
        actual_cpu_load = '95'
        latest_timestamp = datetime.datetime.utcnow() + datetime.timedelta(seconds=200)
        self.cw_mock.get_metric_statistics.return_value = {
            'Datapoints': [
                {'Maximum': actual_cpu_load, 'Timestamp': latest_timestamp},
                {'Maximum': '3', 'Timestamp': datetime.datetime.utcnow()},
                {'Maximum': '8', 'Timestamp': datetime.datetime.utcnow()}
            ]
        }
        stress_duration = 3
        exp_recovery_time = 10
        instance_ids = get_instance_ids_by_count(5)
        metric_delay_secs = 5

        start_time = time.time()
        verify_ec2_stress(instance_ids, stress_duration, expected_cpu_load,
                          metric_delay_secs, 'CPUUtilization', exp_recovery_time)
        end_time = time.time()
        self.assertEqual(round(end_time - start_time), 0)

    @patch('documents.util.scripts.src.cloudwatch_util.time.sleep')
    def test_verify_ec2_stress_metric_wait_time_1_success(self, patch_sleep):
        expected_cpu_load = 95
        actual_cpu_load = '95'
        latest_timestamp = datetime.datetime.utcnow() + datetime.timedelta(seconds=200)
        self.cw_mock.get_metric_statistics.return_value = {
            'Datapoints': [
                {'Maximum': actual_cpu_load, 'Timestamp': latest_timestamp},
                {'Maximum': '3', 'Timestamp': datetime.datetime.utcnow()},
                {'Maximum': '8', 'Timestamp': datetime.datetime.utcnow()}
            ]
        }

        stress_duration = 3
        exp_recovery_time = 1
        instance_ids = get_instance_ids_by_count(5)
        metric_delay_secs = 6

        verify_ec2_stress(instance_ids, stress_duration, expected_cpu_load, metric_delay_secs, 'CPUUtilization',
                          exp_recovery_time)
        patch_sleep.assert_called_once()

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
        latest_timestamp = datetime.datetime.utcnow() + datetime.timedelta(seconds=200)
        self.cw_mock.get_metric_statistics.return_value = {
            'Datapoints': [
                {'Maximum': '10', 'Timestamp': datetime.datetime.utcnow()},
                {'Maximum': '5', 'Timestamp': datetime.datetime.utcnow()},
                {'Maximum': '100', 'Timestamp': latest_timestamp},
                {'Maximum': '7', 'Timestamp': datetime.datetime.utcnow()}
            ]
        }
        dp = get_ec2_metric_max_datapoint('ec2-instance-1', 'CPUUtilization', None, None)
        self.assertEqual(dp, 100)

    def test_get_ec2_cpu_metric_max_datapoint_no_point(self):
        self.cw_mock.get_metric_statistics.return_value = {'Datapoints': []}
        dp = get_ec2_metric_max_datapoint('ec2-instance-1', 'CPUUtilization', None, None)
        self.assertEqual(dp, 0.0)

    def test_verify_alarm_triggered_duration_minutes_success(self):
        self.cw_mock.describe_alarm_history.return_value = {
            'AlarmHistoryItems': [
                {'HistorySummary': 'Alarm updated from OK to ALARM'},
                {'HistorySummary': 'Alarm updated from ALARM to OK'}
            ]
        }

        events = {}
        events['AlarmName'] = 'AlarmName'
        events['DurationInMinutes'] = '1'

        verify_alarm_triggered(events, None)

    def test_verify_alarm_triggered_duration_seconds_success(self):
        self.cw_mock.describe_alarm_history.return_value = {
            'AlarmHistoryItems': [
                {'HistorySummary': 'Alarm updated from OK to ALARM'},
                {'HistorySummary': 'Alarm updated from ALARM to OK'}
            ]
        }

        events = {}
        events['AlarmName'] = 'AlarmName'
        events['DurationInSeconds'] = '60'

        verify_alarm_triggered(events, None)

    def test_verify_alarm_triggered_fail(self):
        self.cw_mock.describe_alarm_history.return_value = {
            'AlarmHistoryItems': [{'HistorySummary': 'Alarm updated from ALARM to OK'}]
        }

        events = {}
        events['AlarmName'] = 'AlarmName'
        events['DurationInMinutes'] = '1'

        self.assertRaises(Exception, verify_alarm_triggered, events, None)

    def test_verify_alarm_triggered_missing_duration(self):
        self.cw_mock.describe_alarm_history.return_value = {
            'AlarmHistoryItems': [{'HistorySummary': 'Alarm updated from ALARM to OK'}]
        }

        events = {}
        events['AlarmName'] = 'AlarmName'

        self.assertRaises(KeyError, verify_alarm_triggered, events, None)

    def test_verify_alarm_triggered_missing_alarm_name(self):
        self.cw_mock.describe_alarm_history.return_value = {
            'AlarmHistoryItems': [{'HistorySummary': 'Alarm updated from ALARM to OK'}]
        }

        events = {}
        events['DurationInMinutes'] = '1'

        self.assertRaises(KeyError, verify_alarm_triggered, events, None)

    def test_get_metric_alarm_threshold_values(self):
        self.cw_mock.describe_alarms.return_value = {
            'MetricAlarms': [{'Threshold': 100}]
        }

        events = {}
        events['AlarmName'] = 'AlarmName'
        response = get_metric_alarm_threshold_values(events, None)
        self.assertEqual(100, response['Threshold'])
        self.assertGreater(100, response['ValueBelowThreshold'])
        self.assertLess(100, response['ValueAboveThreshold'])
