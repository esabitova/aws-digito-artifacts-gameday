import unittest
import pytest
import documents.util.scripts.src.elb_util as elb_util
import documents.util.scripts.test.test_data_provider as test_data_provider
# from botocore.exceptions import ClientError
from unittest.mock import patch, MagicMock

NW_LB_ARN = f"arn:aws:elasticloadbalancing:eu-central-1:{test_data_provider.ACCOUNT_ID}:loadbalancer/net/" \
            f"Netwo-Netwo-1OSTSXGO115F3/faf6ae914c184375"
TARGET_GROUP_ARN = f"arn:aws:elasticloadbalancing:eu-central-1:{test_data_provider.ACCOUNT_ID}:" \
                   f"targetgroup/Netwo-NLBTa-1/1f76413fcf8b3bd7"


def get_target_groups():
    res = {
        "TargetGroups": [
            {
                "TargetGroupArn": TARGET_GROUP_ARN,
                "TargetGroupName": "Netwo-NLBTa-1",
                "Protocol": "TCP",
                "Port": 80,
                "VpcId": test_data_provider.VPC_ID,
                "HealthCheckProtocol": "TCP",
                "HealthCheckPort": "80",
                "HealthCheckEnabled": True,
                "HealthCheckIntervalSeconds": 10,
                "HealthCheckTimeoutSeconds": 10,
                "HealthyThresholdCount": 2,
                "UnhealthyThresholdCount": 2,
                "LoadBalancerArns": [
                    NW_LB_ARN
                ],
                "TargetType": "instance"
            }
        ]
    }
    return [res]


def get_paginate_side_effect(function):
    class PaginateMock(MagicMock):
        def paginate(self, **kwargs):
            return function()

    return PaginateMock


@pytest.mark.unit_test
class TestELBUtil(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('boto3.client')
        self.client = self.patcher.start()
        self.mock_elb = MagicMock()
        self.side_effect_map = {
            'elbv2': self.mock_elb,
        }
        self.client.side_effect = lambda service_name, config=None: self.side_effect_map.get(service_name)

    def tearDown(self):
        self.patcher.stop()

    def test_check_required_params(self):
        events = {
            'test': 'foo'
        }
        required_params = [
            'test',
            'test2'
        ]
        with pytest.raises(KeyError) as key_error:
            elb_util.check_required_params(required_params, events)
        assert 'Requires test2 in events' in str(key_error.value)

    def test_backup_targets__no_targets(self):
        events = {
            "LoadBalancerArn": NW_LB_ARN
        }

        self.mock_elb.get_paginator = get_paginate_side_effect(get_target_groups)
        res = elb_util.backup_targets(events, {})
        self.assertEqual(res,
                         [{'HealthCheckEnabled': True,
                           'HealthCheckIntervalSeconds': 10,
                           'HealthCheckPath': None,
                           'HealthCheckPort': '80',
                           'HealthCheckProtocol': 'TCP',
                           'HealthCheckTimeoutSeconds': 10,
                           'HealthyThresholdCount': 2,
                           'LoadBalancerArn': NW_LB_ARN,
                           'Matcher': {'GrpcCode': None, 'HttpCode': None},
                           'TargetGroupArn': TARGET_GROUP_ARN,
                           'UnhealthyThresholdCount': 2}])

    def test_backup_targets__with_targets(self):
        events = {
            "LoadBalancerArn": NW_LB_ARN,
            "TargetGroupArns": [TARGET_GROUP_ARN]
        }

        self.mock_elb.get_paginator = get_paginate_side_effect(get_target_groups)
        res = elb_util.backup_targets(events, {})
        self.mock_elb.get_paginator = get_paginate_side_effect(get_target_groups)
        res = elb_util.backup_targets(events, {})
        self.assertEqual(res,
                         [{'HealthCheckEnabled': True,
                           'HealthCheckIntervalSeconds': 10,
                           'HealthCheckPath': None,
                           'HealthCheckPort': '80',
                           'HealthCheckProtocol': 'TCP',
                           'HealthCheckTimeoutSeconds': 10,
                           'HealthyThresholdCount': 2,
                           'LoadBalancerArn': NW_LB_ARN,
                           'Matcher': {'GrpcCode': None, 'HttpCode': None},
                           'TargetGroupArn': TARGET_GROUP_ARN,
                           'UnhealthyThresholdCount': 2}])

    def test_break_targets_healthcheck_port(self):
        events = {
            "TargetGroups": [
                {
                    "TargetGroupArn": TARGET_GROUP_ARN,
                    "LoadBalancerArn": NW_LB_ARN,
                    "HealthCheckProtocol": "TCP",
                    "HealthCheckPort": "80",
                    "HealthCheckEnabled": True,
                    "HealthCheckIntervalSeconds": 10,
                    "HealthCheckTimeoutSeconds": 10,
                    "HealthyThresholdCount": 2,
                    "UnhealthyThresholdCount": 2,
                    "Matcher": {}
                }
            ],
            "HealthCheckPort": 65551
        }
        self.mock_elb.modify_target_group.return_value = {}
        elb_util.break_targets_healthcheck_port(events, {})
        for group in events['TargetGroups']:
            self.mock_elb.modify_target_group.assert_called_once_with(
                TargetGroupArn=group['TargetGroupArn'],
                HealthCheckEnabled=True,
                HealthCheckIntervalSeconds=10,
                HealthyThresholdCount=2,
                HealthCheckPort=str(events['HealthCheckPort'])
            )

    def test_restore_targets_healthcheck_port(self):
        events = {
            "TargetGroups": [
                {
                    "TargetGroupArn": TARGET_GROUP_ARN,
                    "LoadBalancerArn": NW_LB_ARN,
                    "HealthCheckProtocol": "TCP",
                    "HealthCheckPort": "80",
                    "HealthCheckEnabled": True,
                    "HealthCheckIntervalSeconds": 10,
                    "HealthCheckTimeoutSeconds": 10,
                    "HealthyThresholdCount": 2,
                    "UnhealthyThresholdCount": 2,
                    "Matcher": {}
                }
            ]
        }
        self.mock_elb.modify_target_group.return_value = {}
        elb_util.restore_targets_healthcheck_port(events, {})
        for group in events['TargetGroups']:
            self.mock_elb.modify_target_group.assert_called_once_with(**group)
