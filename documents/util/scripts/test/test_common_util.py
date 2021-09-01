import datetime
import unittest
from unittest.mock import patch, MagicMock

import pytest
from botocore.exceptions import ClientError

import documents.util.scripts.src.common_util as common_util
import documents.util.scripts.test.test_data_provider as test_data_provider
from documents.util.scripts.test.mock_sleep import MockSleep

TEST_TAG = 'testservice:test:do_something_with_configuration'


@pytest.mark.unit_test
class TestCommonUtil(unittest.TestCase):
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
            'ExecutionId': test_data_provider.AUTOMATION_EXECUTION_ID,
            'Tag': TEST_TAG
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
            TagSpecifications=[
                {'ResourceType': 'security-group',
                 'Tags': [{'Key': 'Digito',
                           'Value': events['Tag']}, ]}])

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

        self.assertEqual(result, {'EmptySecurityGroupId': test_data_provider.SECURITY_GROUP,
                                  'EmptySecurityGroupIdList': [test_data_provider.SECURITY_GROUP]})

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
            'ExecutionId': test_data_provider.AUTOMATION_EXECUTION_ID,
            'Tag': TEST_TAG
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
            TagSpecifications=[
                {'ResourceType': 'security-group',
                 'Tags': [{'Key': 'Digito',
                           'Value': events['Tag']}, ]}])

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

    def test_remove_empty_security_group(self):
        events = {
            'EmptySecurityGroupId': test_data_provider.SECURITY_GROUP
        }

        self.mock_ec2.describe_security_groups.return_value = {
            'SecurityGroups': [
                {
                    'Description': 'Test',
                    'GroupName': 'Test',
                    'GroupId': test_data_provider.SECURITY_GROUP,
                    'VpcId': test_data_provider.VPC_ID
                }
            ]
        }
        self.mock_ec2.delete_security_group.return_value = {
            'ResponseMetadata': {
                'HTTPStatusCode': 200
            }
        }
        common_util.remove_empty_security_group(events, None)
        self.mock_ec2.describe_security_groups.assert_called_once_with(
            Filters=[
                {
                    'Name': 'group-id',
                    'Values': [
                        test_data_provider.SECURITY_GROUP,
                    ]
                },
            ]
        )
        self.mock_ec2.delete_security_group.assert_called_once_with(GroupId=test_data_provider.SECURITY_GROUP)

    @patch('time.sleep')
    def test_remove_empty_security_group_with_timeout(self, patched_sleep):
        mock_sleep = MockSleep()
        patched_sleep.side_effect = mock_sleep.sleep
        events = {
            'EmptySecurityGroupId': test_data_provider.SECURITY_GROUP,
            'Timeout': 1800
        }

        self.mock_ec2.describe_security_groups.return_value = {
            'SecurityGroups': [
                {
                    'Description': 'Test',
                    'GroupName': 'Test',
                    'GroupId': test_data_provider.SECURITY_GROUP,
                    'VpcId': test_data_provider.VPC_ID
                }
            ]
        }
        self.mock_ec2.delete_security_group.side_effect = [
            ClientError(error_response={'Error': {'Type': 'Sender', 'Code': 'DependencyViolation'}},
                        operation_name='DeleteFunction'
                        ),
            ClientError(error_response={'Error': {'Type': 'Sender', 'Code': 'RequestLimitExceeded'}},
                        operation_name='DeleteFunction'
                        ),
            {
                'ResponseMetadata': {
                    'HTTPStatusCode': 200
                }
            }
        ]
        common_util.remove_empty_security_group(events, None)
        self.mock_ec2.describe_security_groups.assert_called_with(
            Filters=[
                {
                    'Name': 'group-id',
                    'Values': [
                        test_data_provider.SECURITY_GROUP,
                    ]
                },
            ]
        )
        self.mock_ec2.delete_security_group.assert_called_with(GroupId=test_data_provider.SECURITY_GROUP)

    def test_remove_empty_security_group_catch_not_found(self):
        events = {
            'EmptySecurityGroupId': test_data_provider.SECURITY_GROUP,
            'Timeout': 1800
        }

        self.mock_ec2.describe_security_groups.return_value = {
            'SecurityGroups': [
                {
                    'Description': 'Test',
                    'GroupName': 'Test',
                    'GroupId': test_data_provider.SECURITY_GROUP,
                    'VpcId': test_data_provider.VPC_ID
                }
            ]
        }
        self.mock_ec2.delete_security_group.side_effect = [
            ClientError(error_response={'Error': {'Type': 'Sender', 'Code': 'InvalidGroup.NotFound'}},
                        operation_name='DeleteFunction'
                        ),
        ]
        common_util.remove_empty_security_group(events, None)
        self.mock_ec2.describe_security_groups.assert_called_once_with(
            Filters=[
                {
                    'Name': 'group-id',
                    'Values': [
                        test_data_provider.SECURITY_GROUP,
                    ]
                },
            ]
        )
        self.mock_ec2.delete_security_group.assert_called_once_with(GroupId=test_data_provider.SECURITY_GROUP)

    def test_remove_empty_security_group_catch_error(self):
        events = {
            'EmptySecurityGroupId': test_data_provider.SECURITY_GROUP,
            'Timeout': 1800
        }

        self.mock_ec2.describe_security_groups.return_value = {
            'SecurityGroups': [
                {
                    'Description': 'Test',
                    'GroupName': 'Test',
                    'GroupId': test_data_provider.SECURITY_GROUP,
                    'VpcId': test_data_provider.VPC_ID
                }
            ]
        }
        self.mock_ec2.delete_security_group.side_effect = [
            ClientError(error_response={'Error': {'Type': 'Sender', 'Code': 'failpols'}},
                        operation_name='DeleteFunction'
                        ),
        ]
        with pytest.raises(ClientError) as error:
            common_util.remove_empty_security_group(events, None)
        self.mock_ec2.describe_security_groups.assert_called_once_with(
            Filters=[
                {
                    'Name': 'group-id',
                    'Values': [
                        test_data_provider.SECURITY_GROUP,
                    ]
                },
            ]
        )
        self.mock_ec2.delete_security_group.assert_called_once_with(GroupId=test_data_provider.SECURITY_GROUP)
        assert 'An error occurred (failpols) when calling the DeleteFunction operation: Unknown' in str(error.value)

    def test_remove_empty_security_group_no_sg_found(self):
        events = {
            'EmptySecurityGroupId': test_data_provider.SECURITY_GROUP
        }

        self.mock_ec2.describe_security_groups.return_value = {
            'SecurityGroups': []
        }
        self.mock_ec2.delete_security_group.return_value = {
            'ResponseMetadata': {
                'HTTPStatusCode': 200
            }
        }
        common_util.remove_empty_security_group(events, None)
        self.mock_ec2.describe_security_groups.assert_called_once_with(
            Filters=[
                {
                    'Name': 'group-id',
                    'Values': [
                        test_data_provider.SECURITY_GROUP,
                    ]
                },
            ]
        )
        self.mock_ec2.delete_security_group.assert_not_called()

    def test_remove_empty_security_group_wrong_params(self):
        events = {}

        with pytest.raises(KeyError) as error:
            common_util.remove_empty_security_group(events, None)

        assert 'Requires EmptySecurityGroupId in events' in str(error.value)

    def test_raise_exception_empty_event(self):
        events = {}

        with pytest.raises(KeyError) as error:
            common_util.raise_exception(events, None)

        assert 'Requires ErrorMessage in events' in str(error.value)

    def test_raise_exception(self):
        events = {'first': '1',
                  'second': '2',
                  'ErrorMessage': "First is {first}, second is {second}"}

        with pytest.raises(AssertionError) as error:
            common_util.raise_exception(events, None)
        assert 'First is 1, second is 2' in str(error.value)

    @patch('time.sleep')
    @patch('time.time')
    def test_remove_empty_security_group_timeout(self, patched_time, patched_sleep):
        events = {
            'EmptySecurityGroupId': test_data_provider.SECURITY_GROUP,
            'Timeout': 1800
        }
        mock_sleep = MockSleep()
        patched_time.side_effect = mock_sleep.time
        patched_sleep.side_effect = mock_sleep.sleep

        self.mock_ec2.describe_security_groups.return_value = {
            'SecurityGroups': [
                {
                    'Description': 'Test',
                    'GroupName': 'Test',
                    'GroupId': test_data_provider.SECURITY_GROUP,
                    'VpcId': test_data_provider.VPC_ID
                }
            ]
        }
        self.mock_ec2.delete_security_group.side_effect = ClientError(
            error_response={'Error': {'Type': 'Sender', 'Code': 'DependencyViolation'}},
            operation_name='DeleteFunction'
        )

        with pytest.raises(TimeoutError) as error:
            common_util.remove_empty_security_group(events, None)
        self.mock_ec2.describe_security_groups.assert_called_with(
            Filters=[
                {
                    'Name': 'group-id',
                    'Values': [
                        test_data_provider.SECURITY_GROUP,
                    ]
                },
            ]
        )
        self.mock_ec2.delete_security_group.assert_called_with(GroupId=test_data_provider.SECURITY_GROUP)
        self.assertEqual(
            f"Security group {events['EmptySecurityGroupId']} couldn't be deleted in {events['Timeout']} seconds",
            str(error.value)
        )
