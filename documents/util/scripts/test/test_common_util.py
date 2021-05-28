import datetime
import unittest
import pytest
from unittest.mock import patch, MagicMock

from botocore.exceptions import ClientError

import documents.util.scripts.test.test_data_provider as test_data_provider
# from documents.util.scripts.test.test_lambda_util import get_lambda_function
import documents.util.scripts.src.common_util as common_util


@pytest.mark.unit_test
class TestLambdaUtil(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('boto3.client')
        self.client = self.patcher.start()
        self.mock_ec2 = MagicMock()
        self.datetime_mock = MagicMock()
        side_effect_map = {
            'ec2': self.mock_ec2
        }

        self.client.side_effect = lambda service_name, config=None: side_effect_map.get(service_name)

    def tearDown(self):
        self.patcher.stop()

    def test_start_time(self):
        with patch('documents.util.scripts.src.common_util.datetime') as mock_date:
            mock_date.now.return_value = datetime.datetime(2021, 5, 28, 15, 7, 50, 327651,
                                                           tzinfo=datetime.timezone.utc)
            result = common_util.start_time({}, None)
            self.assertEqual('2021-05-28T15:07:50.327651+00:00', result)

    def test_recovery_time(self):
        events = {
            'StartTime': '2021-05-28T14:07:50.327651+00:00'
        }
        with patch('documents.util.scripts.src.common_util.datetime') as mock_date:
            mock_date.now.return_value = datetime.datetime(2021, 5, 28, 15, 7, 50, 327651,
                                                           tzinfo=datetime.timezone.utc)
            result = common_util.recovery_time(events, None)
            self.assertEqual(3600, result)

    def test_create_empty_security_group(self):
        events = {
            'VpcId': test_data_provider.VPC_ID,
            'ExecutionId': test_data_provider.AUTOMATION_EXECUTION_ID
        }
        self.mock_ec2.create_security_group.return_value = {
            'GroupId': test_data_provider.SECURITY_GROUP
        }

        self.mock_ec2.revoke_security_group_egress.return_value = {
            'Return': 'True'
        }

        result = common_util.create_empty_security_group(events, None)

        self.mock_ec2.create_security_group.assert_called_once_with(
            Description=f'Empty SG for executionID {events["ExecutionId"]}',
            GroupName=f'EmptySG-{events["ExecutionId"]}',
            VpcId=events['VpcId'],
        )

        self.mock_ec2.revoke_security_group_egress.assert_called_once_with(
            GroupId=test_data_provider.SECURITY_GROUP,
            IpPermissions=[
                {
                    "IpProtocol": "-1",
                    "IpRanges": [
                        {
                            "CidrIp": "0.0.0.0/0"
                        }
                    ],
                    "Ipv6Ranges": [],
                    "PrefixListIds": [],
                    "UserIdGroupPairs": []
                }
            ]
        )

        self.assertEqual(result, {'EmptySecurityGroupId': test_data_provider.SECURITY_GROUP})

    def test_create_empty_security_group_wrong_params(self):
        events = {
            'VpcId': test_data_provider.VPC_ID,
        }

        with pytest.raises(KeyError) as error:
            common_util.create_empty_security_group(events, None)

        assert 'Requires ExecutionId in events' in str(error.value)

    def test_create_empty_security_group_could_not_revoke(self):
        events = {
            'VpcId': test_data_provider.VPC_ID,
            'ExecutionId': test_data_provider.AUTOMATION_EXECUTION_ID
        }
        self.mock_ec2.create_security_group.return_value = {
            'GroupId': test_data_provider.SECURITY_GROUP
        }

        self.mock_ec2.revoke_security_group_egress.return_value = {
            'Return': False
        }

        self.mock_ec2.delete_security_group.return_value = {
            'ResponseMetadata':
                {
                    'HTTPStatusCode': 200
                }
        }

        with pytest.raises(ClientError) as error:
            common_util.create_empty_security_group(events, None)

        self.mock_ec2.create_security_group.assert_called_once_with(
            Description=f'Empty SG for executionID {events["ExecutionId"]}',
            GroupName=f'EmptySG-{events["ExecutionId"]}',
            VpcId=events['VpcId'],
        )

        self.mock_ec2.revoke_security_group_egress.assert_called_once_with(
            GroupId=test_data_provider.SECURITY_GROUP,
            IpPermissions=[
                {
                    "IpProtocol": "-1",
                    "IpRanges": [
                        {
                            "CidrIp": "0.0.0.0/0"
                        }
                    ],
                    "Ipv6Ranges": [],
                    "PrefixListIds": [],
                    "UserIdGroupPairs": []
                }
            ]
        )

        assert 'CouldNotRevoke' in str(error.value)

    #
    # def test_remove_empty_security_group(self):
    #     events = {
    #         'EmptySecurityGroupId': test_data_provider.SECURITY_GROUP
    #     }
    #
    #     self.mock_ec2.describe_security_groups.return_value = get_lambda_function()

    def test_remove_empty_security_group_wrong_params(self):
        events = {}

        with pytest.raises(KeyError) as error:
            common_util.create_empty_security_group(events, None)

        assert 'Requires VpcId in events' in str(error.value)
