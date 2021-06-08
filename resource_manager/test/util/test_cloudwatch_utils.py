import unittest
from unittest.mock import MagicMock, call, patch

import pytest
import resource_manager.src.util.boto3_client_factory as client_factory
from resource_manager.src.util.cloudwatch_utils import (
    _delete_alarms, _describe_metric_alarms,
    _execute_boto3_cloudwatch, _execute_boto3_cloudwatch_paginator,
    delete_alarms_for_dynamo_db_table, get_metric_alarms_for_table)

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
class TestCloudWatchUtils(unittest.TestCase):

    def setUp(self):
        self.session_mock = MagicMock()
        self.cw_mock = MagicMock()
        self.client_side_effect_map = {
            'cloudwatch': self.cw_mock
        }
        self.session_mock.client.side_effect = lambda service_name, config=None: \
            self.client_side_effect_map.get(service_name)
        self.cw_mock.describe_alarms.return_value = \
            DESCRIBE_ALARMS_RESPONSE
        self.cw_mock.delete_alarms.return_value = \
            GENERIC_SUCCESS_RESULT

    def tearDown(self):
        # Clean client factory cache after each test.
        client_factory.clients = {}
        client_factory.resources = {}

    def test__execute_boto3_cloudwatch_raises_exception(self):
        with self.assertRaises(ValueError):
            _execute_boto3_cloudwatch(boto3_session=self.session_mock,
                                      delegate=lambda x: {'ResponseMetadata': {'HTTPStatusCode': 500}})

    def test__execute_boto3_cloudwatch_paginator(self):
        paginator_mock = MagicMock()
        self.cw_mock.get_paginator.return_value = paginator_mock

        paginate_mock = MagicMock()
        paginator_mock.paginate.return_value = paginate_mock
        paginate_mock.search.return_value = iter(['some value'])

        _execute_boto3_cloudwatch_paginator(boto3_session=self.session_mock,
                                            func_name='my_func',
                                            search_exp='Collection[]',
                                            value1='abc')
        self.cw_mock.get_paginator.assert_called_with('my_func')
        paginator_mock.paginate.assert_called_with(value1='abc')
        paginate_mock.search.assert_called_with('Collection[]')

    def test__execute_boto3_cloudwatch_paginator__page_iterator(self):
        paginator_mock = MagicMock()
        self.cw_mock.get_paginator.return_value = paginator_mock

        paginate_mock = MagicMock()
        paginator_mock.paginate.return_value = paginate_mock
        paginate_mock.search.return_value = iter(['some value'])

        _execute_boto3_cloudwatch_paginator(boto3_session=self.session_mock, func_name='my_func', value1='abc')
        self.cw_mock.get_paginator.assert_called_with('my_func')
        paginator_mock.paginate.assert_called_with(value1='abc')
        paginate_mock.search.assert_not_called()

    def test__delete_metric_alarms(self):

        result = _delete_alarms(boto3_session=self.session_mock, alarms_to_delete=['alarm'])

        self.cw_mock.delete_alarms.assert_called_with(AlarmNames=['alarm'])
        self.assertEqual(result, GENERIC_SUCCESS_RESULT)

    @patch('resource_manager.src.util.cloudwatch_utils._execute_boto3_cloudwatch_paginator',
           return_value=iter(DESCRIBE_ALARMS_RESPONSE['MetricAlarms']))
    def test__describe_metric_alarms(self, paginator_mock):

        result = _describe_metric_alarms(boto3_session=self.session_mock)

        self.assertEqual(list(result), DESCRIBE_ALARMS_RESPONSE['MetricAlarms'])
        paginator_mock.assert_has_calls(
            [call(boto3_session=self.session_mock,
                  func_name='describe_alarms',
                  search_exp='MetricAlarms[]',
                  AlarmTypes=['MetricAlarm'])])

    @patch('resource_manager.src.util.cloudwatch_utils._execute_boto3_cloudwatch_paginator',
           return_value=iter(DESCRIBE_ALARMS_RESPONSE['MetricAlarms']))
    def test__describe_metric_alarms__with_alarm_names(self, paginator_mock):

        result = _describe_metric_alarms(boto3_session=self.session_mock, alarm_names=['alarm_name1'])

        self.assertEqual(list(result), DESCRIBE_ALARMS_RESPONSE['MetricAlarms'])
        paginator_mock.assert_has_calls(
            [call(boto3_session=self.session_mock,
                  func_name='describe_alarms',
                  search_exp='MetricAlarms[]',
                  AlarmTypes=['MetricAlarm'],
                  AlarmNames=['alarm_name1'])])

    @patch('resource_manager.src.util.cloudwatch_utils._describe_metric_alarms',
           return_value=iter(DESCRIBE_ALARMS_RESPONSE['MetricAlarms']))
    def test_get_metric_alarms_for_table(self, describe_mock):

        result = get_metric_alarms_for_table(boto3_session=self.session_mock,
                                             table_name='source_table',
                                             alarms_names=['alarm_name1'])

        self.assertEqual(list(result), [alarm for alarm in DESCRIBE_ALARMS_RESPONSE['MetricAlarms']])
        describe_mock.assert_has_calls(
            [call(boto3_session=self.session_mock,
                  alarm_names=['alarm_name1'])])

    @patch('resource_manager.src.util.cloudwatch_utils.get_metric_alarms_for_table',
           return_value=iter([alarm for alarm in DESCRIBE_ALARMS_RESPONSE['MetricAlarms']]))
    @patch('resource_manager.src.util.cloudwatch_utils._delete_alarms',
           return_value=DESCRIBE_ALARMS_RESPONSE)
    def test_delete_alarms_for_dynamo_db_table(self, describe_mock, delete_mock):

        delete_alarms_for_dynamo_db_table(boto3_session=self.session_mock,
                                          table_name="source_table")

        describe_mock.assert_called()
        delete_mock.assert_called()

    @patch('resource_manager.src.util.cloudwatch_utils.get_metric_alarms_for_table',
           return_value=iter([]))
    @patch('resource_manager.src.util.cloudwatch_utils._delete_alarms',
           return_value=DESCRIBE_ALARMS_RESPONSE)
    def test_delete_alarms_for_dynamo_db_table__empty_resp(self, delete_mock, describe_mock):

        delete_alarms_for_dynamo_db_table(boto3_session=self.session_mock,
                                          table_name="source_table")

        describe_mock.assert_called()
        self.assertFalse(delete_mock.called)
