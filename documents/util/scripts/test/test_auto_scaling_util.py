
import unittest
from unittest.mock import MagicMock, patch
from parameterized import parameterized

import pytest
from documents.util.scripts.src.auto_scaling_util import (
    _execute_boto3_auto_scaling,
    _register_scalable_target,
    register_scaling_targets)

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

        self.application_autoscaling_client_mock.register_scalable_target.return_value = \
            DESCRIBE_SCALABLE_TARGETS_RESPONSE

    def tearDown(self):
        self.patcher.stop()

    def test__execute_boto3_dynamodb_raises_exception(self):
        with self.assertRaises(ValueError):
            _execute_boto3_auto_scaling(lambda x: {'ResponseMetadata': {'HTTPStatusCode': 500}})

    @parameterized.expand([
        {'events': {}},
        {'events': {'TableName': 'my_table'}},
    ])
    def test_register_scaling_targets_raises_exception(self, events):
        with self.assertRaises(KeyError):
            register_scaling_targets(events=events, context={})

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

    @patch('documents.util.scripts.src.auto_scaling_util._register_scalable_target',
           return_value={})
    def test_register_scaling_targets(self, register_mock):
        events = {
            "TableName": "my_table",
            "ScalableTargets":
            DESCRIBE_SCALABLE_TARGETS_RESPONSE['ScalableTargets']
        }
        register_scaling_targets(events=events, context={})

        register_mock.assert_called_with(table_name='my_table',
                                         dimension='dimension',
                                         max_cap=5,
                                         min_cap=1)
