
import unittest
from unittest.mock import MagicMock, patch
import resource_manager.src.util.boto3_client_factory as client_factory

import pytest
from resource_manager.src.util.auto_scaling_utils import (
    _deregister_scalable_target_for_dynamodb_table, _describe_scalable_targets_for_dynamodb_table,
    _execute_boto3_auto_scaling,
    deregister_all_scaling_target_all_dynamodb_table)

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
class TestAutoScalingUtils(unittest.TestCase):
    def setUp(self):
        self.session_mock = MagicMock()
        self.application_autoscaling_client_mock = MagicMock()
        self.client_side_effect_map = {
            'application-autoscaling': self.application_autoscaling_client_mock
        }
        self.session_mock.client.side_effect = lambda service_name, config=None: \
            self.client_side_effect_map.get(service_name)

        self.application_autoscaling_client_mock.describe_scalable_targets.return_value = \
            DESCRIBE_SCALABLE_TARGETS_RESPONSE
        self.application_autoscaling_client_mock.deregister_scalable_target.return_value = \
            GENERIC_SUCCESS_RESULT

    def tearDown(self):
        # Clean client factory cache after each test.
        client_factory.clients = {}
        client_factory.resources = {}

    def test__execute_boto3_dynamodb_raises_exception(self):
        with self.assertRaises(ValueError):
            _execute_boto3_auto_scaling(self.session_mock, lambda x: {'ResponseMetadata': {'HTTPStatusCode': 500}})

    def test__describe_scalable_targets(self):

        result = _describe_scalable_targets_for_dynamodb_table(self.session_mock, table_name='my_table')

        self.application_autoscaling_client_mock\
            .describe_scalable_targets\
            .assert_called_with(ServiceNamespace='dynamodb',
                                ResourceIds=['table/my_table'])
        self.assertEquals(result, DESCRIBE_SCALABLE_TARGETS_RESPONSE)

    def test__deregister_scalable_target_for_dynamodb_table(self):

        _deregister_scalable_target_for_dynamodb_table(self.session_mock, table_name='my_table',
                                                       dimension='my_dimension')

        self.application_autoscaling_client_mock\
            .deregister_scalable_target\
            .assert_called_with(ServiceNamespace='dynamodb',
                                ScalableDimension='my_dimension',
                                ResourceId='table/my_table')

    @patch('resource_manager.src.util.auto_scaling_utils._describe_scalable_targets',
           return_value=DESCRIBE_SCALABLE_TARGETS_RESPONSE)
    @patch('resource_manager.src.util.auto_scaling_utils._deregister_scalable_target_for_dynamodb_table',
           return_value=GENERIC_SUCCESS_RESULT)
    def test_deregister_all_scaling_target_all_dynamodb_table(self, deregister_mock, describe_mock):
        deregister_all_scaling_target_all_dynamodb_table(self.session_mock, 'my_table')

        describe_mock.assert_called_with(boto3_session=self.session_mock, table_name='my_table')
        deregister_mock.assert_called_with(boto3_session=self.session_mock, table_name='my_table',
                                           dimension='dimension')
