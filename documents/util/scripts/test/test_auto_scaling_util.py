
import unittest
from unittest.mock import MagicMock, patch

import pytest
from documents.util.scripts.src.auto_scaling_util import (
    _describe_scalable_targets, _execute_boto3_auto_scaling,
    _register_scalable_target, copy_scaling_targets)
from parameterized import parameterized

GENERIC_SUCCESS_RESULT = {
    "ResponseMetadata": {
        "HTTPStatusCode": 200
    }
}
DESCRIBE_SCALABLE_TARGETS_RESPONSE = {
    **GENERIC_SUCCESS_RESULT,
    "NextToken": "string",
    "ScalableTargets": [
        {
            "CreationTime": 12,
            "MaxCapacity": 5,
            "MinCapacity": 1,
            "ResourceId": "table/my_table",
            "RoleARN": "string",
            "ScalableDimension": "dimension",
            "ServiceNamespace": "dynamodb",
            "SuspendedState": {
                "DynamicScalingInSuspended": True,
                "DynamicScalingOutSuspended": True,
                "ScheduledScalingSuspended": True
            }
        }
    ]
}


@pytest.mark.unit_test
class TestAutoScalingUtil(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('boto3.client')
        self.client = self.patcher.start()
        self.application_autoscaling_client_mock = MagicMock()
        self.side_effect_map = {
            'application-autoscaling': self.application_autoscaling_client_mock
        }
        self.client.side_effect = lambda service_name: self.side_effect_map.get(service_name)

        self.application_autoscaling_client_mock.describe_scalable_targets.return_value = \
            DESCRIBE_SCALABLE_TARGETS_RESPONSE
        self.application_autoscaling_client_mock.register_scalable_target.return_value = \
            DESCRIBE_SCALABLE_TARGETS_RESPONSE

    def tearDown(self):
        self.patcher.stop()

    def test__execute_boto3_dynamodb_raises_exception(self):
        with self.assertRaises(ValueError):
            _execute_boto3_auto_scaling(lambda x: {'ResponseMetadata': {'HTTPStatusCode': 500}})

    @parameterized.expand([({}, {}), ({'SourceTableName': 'my_table'}, {})])
    def test_copy_scaling_targets_raises_exception(self, events, context):
        with self.assertRaises(KeyError):
            copy_scaling_targets(events=events, context=context)

    def test__describe_scalable_targets(self):

        result = _describe_scalable_targets(table_name='my_table')

        self.application_autoscaling_client_mock\
            .describe_scalable_targets\
            .assert_called_with(ServiceNamespace='dynamodb',
                                ResourceIds=['table/my_table'])
        self.assertEquals(result, DESCRIBE_SCALABLE_TARGETS_RESPONSE)

    def test__register_scalable_target(self):

        result = _register_scalable_target(table_name='my_table',
                                           dimension='my_dimension',
                                           max_cap=5,
                                           min_cap=1)

        self.application_autoscaling_client_mock\
            .register_scalable_target\
            .assert_called_with(ServiceNamespace='dynamodb',
                                ScalableDimension='my_dimension',
                                MaxCapacity=5,
                                MinCapacity=1,
                                ResourceId='table/my_table')
        self.assertEquals(result, DESCRIBE_SCALABLE_TARGETS_RESPONSE)

    @patch('documents.util.scripts.src.auto_scaling_util._describe_scalable_targets',
           return_value=DESCRIBE_SCALABLE_TARGETS_RESPONSE)
    @patch('documents.util.scripts.src.auto_scaling_util._register_scalable_target',
           return_value={})
    def test_copy_scaling_targets(self, register_mock, describe_mock):
        events = {
            "SourceTableName": "my_table",
            "TargetTableName": "my_table_target"
        }
        result = copy_scaling_targets(events=events, context={})

        self.assertEqual(result, [{"ScalableDimension": "dimension", "MinCapacity": 1, "MaxCapacity": 5}])
        describe_mock.assert_called_with(table_name='my_table')
        register_mock.assert_called_with(table_name='my_table_target',
                                         dimension='dimension',
                                         max_cap=5,
                                         min_cap=1)
