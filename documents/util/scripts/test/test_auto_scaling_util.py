
import unittest
from unittest.mock import MagicMock, patch

import pytest
from documents.util.scripts.src.auto_scaling_util import (
    _describe_scalable_targets, _execute_boto3_auto_scaling,
    _register_scalable_target, copy_scaling_targets,
    _execute_boto3_auto_scaling_paginator)
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
            "RoleARN": "my_role_arn",
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
        self.client.side_effect = lambda service_name, config: self.side_effect_map.get(service_name)

        self.application_autoscaling_client_mock.describe_scalable_targets.return_value = \
            DESCRIBE_SCALABLE_TARGETS_RESPONSE
        self.application_autoscaling_client_mock.register_scalable_target.return_value = \
            DESCRIBE_SCALABLE_TARGETS_RESPONSE

    def tearDown(self):
        self.patcher.stop()

    def test__execute_boto3_auto_scaling_paginator(self):
        paginator_mock = MagicMock()
        self.application_autoscaling_client_mock.get_paginator.return_value = paginator_mock

        paginate_mock = MagicMock()
        paginator_mock.paginate.return_value = paginate_mock
        paginate_mock.search.return_value = iter(['some value'])

        _execute_boto3_auto_scaling_paginator(func_name='my_func', search_exp='Collection[]', value1='abc')
        self.application_autoscaling_client_mock.get_paginator.assert_called_with('my_func')
        paginator_mock.paginate.assert_called_with(value1='abc')
        paginate_mock.search.assert_called_with('Collection[]')

    def test__execute_boto3_auto_scaling_paginator__page_iterator(self):
        paginator_mock = MagicMock()
        self.application_autoscaling_client_mock.get_paginator.return_value = paginator_mock

        paginate_mock = MagicMock()
        paginator_mock.paginate.return_value = paginate_mock
        paginate_mock.search.return_value = iter(['some value'])

        _execute_boto3_auto_scaling_paginator(func_name='my_func', value1='abc')
        self.application_autoscaling_client_mock.get_paginator.assert_called_with('my_func')
        paginator_mock.paginate.assert_called_with(value1='abc')
        paginate_mock.search.assert_not_called()

    def test__execute_boto3_dynamodb_raises_exception(self):
        with self.assertRaises(ValueError):
            _execute_boto3_auto_scaling(lambda x: {'ResponseMetadata': {'HTTPStatusCode': 500}})

    @parameterized.expand([({}, {}), ({'SourceTableName': 'my_table'}, {})])
    def test_copy_scaling_targets_raises_exception(self, events, context):
        with self.assertRaises(KeyError):
            copy_scaling_targets(events=events, context=context)

    @patch('documents.util.scripts.src.auto_scaling_util._execute_boto3_auto_scaling_paginator',
           return_value=iter(DESCRIBE_SCALABLE_TARGETS_RESPONSE['ScalableTargets']))
    def test__describe_scalable_targets(self, paginator_mock):

        result = _describe_scalable_targets(table_name='my_table')

        paginator_mock(func_name='describe_scalable_targets',
                       search_exp='ScalableTargets[]',
                       ServiceNamespace='dynamodb',
                       ResourceIds=['table/my_table'])
        self.assertEquals(list(result), DESCRIBE_SCALABLE_TARGETS_RESPONSE['ScalableTargets'])

    def test__register_scalable_target(self):

        result = _register_scalable_target(table_name='my_table',
                                           dimension='my_dimension',
                                           max_cap=5,
                                           min_cap=1,
                                           role_arn="arn")

        self.application_autoscaling_client_mock\
            .register_scalable_target\
            .assert_called_with(ServiceNamespace='dynamodb',
                                ScalableDimension='my_dimension',
                                MaxCapacity=5,
                                MinCapacity=1,
                                ResourceId='table/my_table',
                                RoleARN='arn')
        self.assertEquals(result, DESCRIBE_SCALABLE_TARGETS_RESPONSE)

    @patch('documents.util.scripts.src.auto_scaling_util._describe_scalable_targets',
           return_value=iter(DESCRIBE_SCALABLE_TARGETS_RESPONSE['ScalableTargets']))
    @patch('documents.util.scripts.src.auto_scaling_util._register_scalable_target',
           return_value={})
    def test_copy_scaling_targets(self, register_mock, describe_mock):
        events = {
            "SourceTableName": "my_table",
            "TargetTableName": "my_table_target"
        }
        result = copy_scaling_targets(events=events, context={})

        self.assertEqual(result, [{"ScalableDimension": "dimension", "MinCapacity": 1,
                         "MaxCapacity": 5, 'RoleARN': 'my_role_arn'}])
        describe_mock.assert_called_with(table_name='my_table')
        register_mock.assert_called_with(table_name='my_table_target',
                                         dimension='dimension',
                                         max_cap=5,
                                         min_cap=1,
                                         role_arn='my_role_arn')
