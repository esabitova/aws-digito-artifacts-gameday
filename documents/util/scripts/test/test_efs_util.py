import unittest
import pytest
import documents.util.scripts.src.efs_util as efs_util
import documents.util.scripts.test.test_data_provider as test_data_provider
from botocore.exceptions import ClientError
from unittest.mock import patch, MagicMock, call

MT_ID = 'fsmt-testtest'
EFS_SG_ID = 'sg-testtesttesttest'
MT_TO_SG_MAP = [f"{MT_ID}:{EFS_SG_ID}", f"{MT_ID}2:{EFS_SG_ID},{EFS_SG_ID}2"]
FS_ID = 'fs-testtest'


def get_sample_describe_mount_targets(max_items=None, MountTargetId=None):
    result = \
        {
            'MountTargets': [
                {
                    "OwnerId": f"{test_data_provider.ACCOUNT_ID}",
                    "MountTargetId": f"{MT_ID}",
                    "FileSystemId": f"{FS_ID}",
                    "SubnetId": f"{test_data_provider.APPLICATION_SUBNET_ID}",
                    "LifeCycleState": "available",
                    "IpAddress": "10.0.0.18",
                    "NetworkInterfaceId": "eni-testtesttesttest",
                    "AvailabilityZoneId": "euw3-az2",
                    "AvailabilityZoneName": "eu-west-3b",
                    "VpcId": f"{test_data_provider.VPC_ID}"
                },
                {
                    "OwnerId": f"{test_data_provider.ACCOUNT_ID}",
                    "MountTargetId": f"{MT_ID}2",
                    "FileSystemId": f"{FS_ID}",
                    "SubnetId": f"{test_data_provider.APPLICATION_SUBNET_ID}",
                    "LifeCycleState": "available",
                    "IpAddress": "10.0.0.19",
                    "NetworkInterfaceId": "eni-testtesttesttes2",
                    "AvailabilityZoneId": "euw3-az2",
                    "AvailabilityZoneName": "eu-west-3b",
                    "VpcId": f"{test_data_provider.VPC_ID}"
                },
                {
                    "OwnerId": f"{test_data_provider.ACCOUNT_ID}",
                    "MountTargetId": f"{MT_ID}3",
                    "FileSystemId": f"{FS_ID}",
                    "SubnetId": f"{test_data_provider.APPLICATION_SUBNET_ID}",
                    "LifeCycleState": "available",
                    "IpAddress": "10.0.0.20",
                    "NetworkInterfaceId": "eni-testtesttesttes3",
                    "AvailabilityZoneId": "euw3-az1",
                    "AvailabilityZoneName": "eu-west-3a",
                    "VpcId": f"{test_data_provider.VPC_ID}"
                },
                {
                    "OwnerId": f"{test_data_provider.ACCOUNT_ID}",
                    "MountTargetId": f"{MT_ID}4",
                    "FileSystemId": f"{FS_ID}2",
                    "SubnetId": f"{test_data_provider.APPLICATION_SUBNET_ID}",
                    "LifeCycleState": "available",
                    "IpAddress": "10.0.0.21",
                    "NetworkInterfaceId": "eni-testtesttesttes4",
                    "AvailabilityZoneId": "euw3-az1",
                    "AvailabilityZoneName": "eu-west-3a",
                    "VpcId": f"{test_data_provider.VPC_ID}"
                }
            ],
            'NextMarker': 'string'
        }
    if MountTargetId:
        result = {
            'MountTargets': [k for k in result['MountTargets'] if k['MountTargetId'] == MountTargetId]
        }
        if not result['MountTargets']:
            raise ClientError(
                error_response={"Error": {
                    "Code": "MountTargetNotFound",
                    "Message": f"Mount target '{MountTargetId}' does not exist."
                }
                },
                operation_name='DescribeMountTargets'
            )
        return result
    if max_items:
        return {'MountTargets': result['MountTargets'][:max_items]}
    return result


def get_sample_describe_mount_target_security_groups(MountTargetId=None):
    sg_not_split = [k.split(":")[1] for k in MT_TO_SG_MAP if k.split(":")[0] == MountTargetId]
    result = \
        {
            "SecurityGroups": []
        }
    if not sg_not_split:
        raise ClientError(
            error_response={"Error": {
                "Code": "MountTargetNotFound",
                "Message": f"Mount target '{MountTargetId}' does not exist."
            }
            },
            operation_name='DescribeMountTargetSecurityGroups'
        )
    for i in sg_not_split:
        result['SecurityGroups'].extend(i.split('.'))

    return result


@pytest.mark.unit_test
class TestEFSUtil(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('boto3.client')
        self.client = self.patcher.start()
        self.mock_efs = MagicMock()
        self.mock_ec2 = MagicMock()
        self.side_effect_map = {
            'efs': self.mock_efs,
            'ec2': self.mock_ec2
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
            efs_util.check_required_params(required_params, events)
        assert 'Requires test2 in events' in str(key_error.value)

    def test_revert_fs_security_groups(self):
        events = {
            'MountTargetIdToSecurityGroupsMap': MT_TO_SG_MAP,
            'ExecutionId': test_data_provider.AUTOMATION_EXECUTION_ID
        }
        self.mock_efs.modify_mount_target_security_groups.return_value = {}
        self.mock_ec2.delete_security_group.return_value = {}
        efs_util.revert_fs_security_groups(events, None)
        expected_calls = []
        for mt_map in events['MountTargetIdToSecurityGroupsMap']:
            mount_target, security_groups_str = mt_map.split(':', 2)
            security_groups_list = security_groups_str.split(',')
            expected_calls.append(call.modify_mount_target_security_groups(
                MountTargetId=mount_target,
                SecurityGroups=security_groups_list
            ))
        self.mock_efs.modify_mount_target_security_groups.assert_has_calls(
            expected_calls
        )

    def test_revert_fs_security_groups_empty_sg(self):
        events = {
            'MountTargetIdToSecurityGroupsMap': [f"{MT_ID}:''"],
            'ExecutionId': test_data_provider.AUTOMATION_EXECUTION_ID
        }
        self.mock_efs.modify_mount_target_security_groups.side_effect = ClientError(
            error_response={"Error": {"Code": "BadRequest"}},
            operation_name='ModifyMountTargetSecurityGroups'
        )
        with pytest.raises(ClientError) as key_error:
            efs_util.revert_fs_security_groups(events, None)
        assert 'An error occurred (BadRequest)' in str(key_error.value)

    def test_revert_fs_security_groups_empty_sg_not_exist(self):
        sg_name = f"EmptySG-{MT_ID}-{test_data_provider.AUTOMATION_EXECUTION_ID}"
        events = {
            'MountTargetIdToSecurityGroupsMap': [f"{MT_ID}:{sg_name}"],
            'ExecutionId': test_data_provider.AUTOMATION_EXECUTION_ID
        }
        self.mock_ec2.describe_security_groups.side_effect = ClientError(
            error_response={"Error": {"Code": "InvalidGroup.NotFound"}},
            operation_name='DescribeSecurityGroups'
        )
        efs_util.revert_fs_security_groups(events, None)
        self.mock_ec2.describe_security_groups.assert_called_once_with(
            Filters=[
                {
                    'Name': 'group-name',
                    'Values': [
                        sg_name,
                    ]
                }
            ]
        )

    def test_revert_fs_security_groups_empty_sg_smth_wrong(self):
        sg_name = f"EmptySG-{MT_ID}-{test_data_provider.AUTOMATION_EXECUTION_ID}"
        events = {
            'MountTargetIdToSecurityGroupsMap': [f"{MT_ID}:{sg_name}"],
            'ExecutionId': test_data_provider.AUTOMATION_EXECUTION_ID
        }
        self.mock_ec2.describe_security_groups.side_effect = ClientError(
            error_response={"Error": {"Code": "BadRequest"}},
            operation_name='DescribeSecurityGroups'
        )
        with pytest.raises(ClientError) as key_error:
            efs_util.revert_fs_security_groups(events, None)
        self.mock_ec2.describe_security_groups.assert_called_once_with(
            Filters=[
                {
                    'Name': 'group-name',
                    'Values': [
                        sg_name,
                    ]
                }
            ]
        )

        assert 'An error occurred (BadRequest)' in str(key_error.value)

    def test_search_for_mount_target_ids_all(self):
        events = {
            'FileSystemId': FS_ID
        }
        self.mock_efs.describe_mount_targets.return_value = get_sample_describe_mount_targets(max_items=1)
        result = efs_util.search_for_mount_target_ids(events, None)
        self.mock_efs.describe_mount_targets.assert_called_once_with(
            FileSystemId=events['FileSystemId'],
            MaxItems=1
        )
        self.assertEqual(events['FileSystemId'], result['FileSystemId'])
        self.assertEqual([get_sample_describe_mount_targets(max_items=1)['MountTargets'][0]['MountTargetId']],
                         result['MountTargetIds'])

    def test_search_for_mount_target_ids_specified(self):
        events = {
            'FileSystemId': FS_ID,
            'MountTargetIds': [MT_ID, f"{MT_ID}2"]
        }
        self.mock_efs.describe_mount_targets.side_effect = get_sample_describe_mount_targets
        result = efs_util.search_for_mount_target_ids(events, None)
        expected_calls = []
        for mt in events['MountTargetIds']:
            expected_calls.append(call.describe_mount_targets(
                MountTargetId=mt
            ))
        self.mock_efs.describe_mount_targets.assert_has_calls(
            expected_calls
        )
        self.assertEqual(events, result)

    def test_search_for_mount_target_ids_specified_foreign_mt_id(self):
        events = {
            'FileSystemId': FS_ID,
            'MountTargetIds': [MT_ID, f"{MT_ID}4"]
        }
        self.mock_efs.describe_mount_targets.side_effect = get_sample_describe_mount_targets
        with pytest.raises(AssertionError) as assert_error:
            efs_util.search_for_mount_target_ids(events, None)
        self.mock_efs.describe_mount_targets.assert_called_with(
            MountTargetId=f"{MT_ID}4"
        )
        assert f"MountTarget {MT_ID}4 doesn't belong to filesystem {FS_ID}" in str(assert_error.value)

    def test_search_for_mount_target_ids_specified_wrong_mt_id(self):
        events = {
            'FileSystemId': FS_ID,
            'MountTargetIds': [MT_ID, f"{MT_ID}5"]
        }
        self.mock_efs.describe_mount_targets.side_effect = get_sample_describe_mount_targets
        with pytest.raises(ClientError) as client_error:
            efs_util.search_for_mount_target_ids(events, None)
        self.mock_efs.describe_mount_targets.assert_called_with(
            MountTargetId=f"{MT_ID}5"
        )
        assert f"An error occurred (MountTargetNotFound) when calling the DescribeMountTargets operation: " \
               f"Mount target '{MT_ID}5' does not exist." in str(client_error.value)

    def test_list_security_groups_for_mount_targets(self):
        events = {
            'MountTargetIds': [MT_ID, f"{MT_ID}2"]
        }
        self.mock_efs.describe_mount_target_security_groups.side_effect = \
            get_sample_describe_mount_target_security_groups
        result = efs_util.list_security_groups_for_mount_targets(events, None)
        expected_calls = []
        for mt in events['MountTargetIds']:
            expected_calls.append(call.describe_mount_targets(
                MountTargetId=mt
            ))
        self.mock_efs.describe_mount_target_security_groups.assert_has_calls(
            expected_calls
        )
        self.assertEqual({
            'MountTargetIdToSecurityGroupsMap': MT_TO_SG_MAP
        }, result)

    def test_list_security_groups_for_mount_targets_wrong_mt_id(self):
        events = {
            'MountTargetIds': [MT_ID, f"{MT_ID}5"]
        }
        self.mock_efs.describe_mount_target_security_groups.side_effect = \
            get_sample_describe_mount_target_security_groups
        with pytest.raises(ClientError) as client_error:
            efs_util.list_security_groups_for_mount_targets(events, None)
        self.mock_efs.describe_mount_target_security_groups.assert_called_with(
            MountTargetId=f"{MT_ID}5"
        )
        assert f"An error occurred (MountTargetNotFound) when calling the DescribeMountTargetSecurityGroups " \
               f"operation: Mount target '{MT_ID}5' does not exist." in str(client_error.value)

    def test_empty_security_groups_for_mount_targets(self):
        events = {
            'MountTargetIds': [MT_ID, f"{MT_ID}3"],
            'ExecutionId': test_data_provider.AUTOMATION_EXECUTION_ID
        }
        self.mock_efs.describe_mount_targets.return_value = get_sample_describe_mount_targets()
        self.mock_ec2.create_security_group.return_value = {'GroupId': 'Test'}
        self.mock_efs.modify_mount_target_security_groups.return_value = {}

        expected_efs_describe_mount_targets_calls = []
        expected_ec2_create_security_group_calls = []
        expected_efs_modify_mount_target_security_groups_calls = []

        for mount_target in events['MountTargetIds']:
            self.mock_ec2.modify_mount_target_security_groups.return_value.create_security_group = {
                'GroupId': f'sg-{mount_target}'
            }
            expected_ec2_create_security_group_calls.append(call.describe_mount_targets(
                Description='Empty SG for test efs:test:break_security_group:2020-09-21',
                GroupName=f'EmptySG-{mount_target}-{events["ExecutionId"]}',
                VpcId=f"{test_data_provider.VPC_ID}",
            ))

            expected_efs_describe_mount_targets_calls.append(call.create_security_group(
                MountTargetId=mount_target
            ))

            expected_efs_modify_mount_target_security_groups_calls.append(call.modify_mount_target_security_groups(
                MountTargetId=mount_target,
                SecurityGroups=['Test']
            ))
        efs_util.empty_security_groups_for_mount_targets(events, None)
        self.mock_efs.describe_mount_targets.assert_has_calls(
            expected_efs_describe_mount_targets_calls
        )
        self.mock_ec2.create_security_group.assert_has_calls(
            expected_ec2_create_security_group_calls
        )
        self.mock_efs.modify_mount_target_security_groups.assert_has_calls(
            expected_efs_modify_mount_target_security_groups_calls
        )

    def test_empty_security_groups_for_mount_targets_empty_mt_list(self):
        events = {
            'MountTargetIds': [],
            'EmptySecurityGroup': 'sg-fffffffffffffffff',
            'ExecutionId': test_data_provider.AUTOMATION_EXECUTION_ID
        }
        self.mock_efs.modify_mount_target_security_groups.return_value = {}
        with pytest.raises(AssertionError) as error:
            efs_util.empty_security_groups_for_mount_targets(events, None)

        assert "MountTargetIds parameter is empty. It past contain at least one MountTarget" in str(error.value)

    def test_empty_security_groups_for_mount_targets_empty_wrong_mt(self):
        events = {
            'MountTargetIds': ['filthy'],
            'EmptySecurityGroup': 'sg-fffffffffffffffff',
            'ExecutionId': test_data_provider.AUTOMATION_EXECUTION_ID
        }
        self.mock_efs.modify_mount_target_security_groups.side_effect = ClientError(
            error_response={
                "Error":
                {
                    "Code": "MountTargetNotFound",
                    "Message": "Mount target 'filthy' does not exist."
                }
            },
            operation_name='ModifyMountTargetSecurityGroups'
        )
        with pytest.raises(ClientError) as error:
            efs_util.empty_security_groups_for_mount_targets(events, None)
        print(str(error.value))
        self.assertEqual(
            "An error occurred (MountTargetNotFound) when calling the ModifyMountTargetSecurityGroups operation: "
            "Mount target 'filthy' does not exist.",
            str(error.value)
        )
