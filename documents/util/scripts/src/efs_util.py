import boto3
import logging

from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def check_required_params(required_params, events):
    for key in required_params:
        if key not in events:
            raise KeyError(f'Requires {key} in events')


def revert_fs_security_groups(events, context):
    required_params = [
        'MountTargetIdToSecurityGroupsMap',
        'ExecutionId'
    ]
    check_required_params(required_params, events)
    efs_client = boto3.client('efs')
    ec2_client = boto3.client('ec2')
    for mt_map in events['MountTargetIdToSecurityGroupsMap']:
        mount_target, security_groups_str = mt_map.split(':', 2)
        security_groups_list = security_groups_str.split(',')
        logger.info(f'Reverting Security groups for MountPoint:{mount_target}')
        efs_client.modify_mount_target_security_groups(
            MountTargetId=mount_target,
            SecurityGroups=security_groups_list
        )
        try:
            logger.info(f'Deleting empty security group: EmptySG-{mount_target}-{events["ExecutionId"]}')
            sg_id = ec2_client.describe_security_groups(
                Filters=[
                    {
                        'Name': 'group-name',
                        'Values': [
                            f"EmptySG-{mount_target}-{events['ExecutionId']}",
                        ]
                    },
                ]
            )['SecurityGroups'][0]['GroupId']
            logger.info(f'Deleting empty security group: {sg_id}')
            ec2_client.delete_security_group(
                GroupId=sg_id
            )
        except ClientError as error:
            if error.response['Error']['Code'] == 'InvalidGroup.NotFound':
                logger.info(f"Empty security group doesn't exist: EmptySG-{mount_target}")
            else:
                raise error


def search_for_mount_target_ids(events, context):
    required_params = [
        'FileSystemId'
    ]
    check_required_params(required_params, events)
    mount_target_ids = []
    efs_client = boto3.client('efs')
    logger.info(f'Getting MountPoints with the following args: {events}')
    if events.get('MountTargetIds'):
        for mt in events['MountTargetIds']:
            mt_info = efs_client.describe_mount_targets(  # no need to paginate, only one MT can have the specified id
                MountTargetId=mt
            )
            if mt_info["MountTargets"][0]['FileSystemId'] != events['FileSystemId']:
                raise AssertionError(f"MountTarget {mt} doesn't belong to filesystem {events['FileSystemId']}")
        mount_target_ids = events['MountTargetIds']
    else:
        # There can be only one MT for each EFS volume in each AZ
        # so we grab any MT and assume it's the only one important for AZ failure test
        # so no need for pagination
        logger.info(f"Getting all MT for FS: {events['FileSystemId']}")
        mount_target = efs_client.describe_mount_targets(
            FileSystemId=events['FileSystemId'],
            MaxItems=1
        )['MountTargets'][0]
        mount_target_ids.append(mount_target['MountTargetId'])
    return {
        'MountTargetIds': mount_target_ids,
        'FileSystemId': events['FileSystemId']
    }


def list_security_groups_for_mount_targets(events, context):
    required_params = [
        'MountTargetIds'
    ]
    check_required_params(required_params, events)

    mt_to_sg_map = []
    efs_client = boto3.client('efs')

    for mt in events['MountTargetIds']:
        response = efs_client.describe_mount_target_security_groups(
            MountTargetId=mt
        )
        mt_to_sg_map.append(f"{mt}:{','.join(response['SecurityGroups'])}")
    return {
        'MountTargetIdToSecurityGroupsMap': mt_to_sg_map
    }


def empty_security_groups_for_mount_targets(events, context):
    required_params = [
        'MountTargetIds',
        'ExecutionId'
    ]
    check_required_params(required_params, events)
    efs_client = boto3.client('efs')
    ec2_client = boto3.client('ec2')

    if not events['MountTargetIds']:
        raise AssertionError('MountTargetIds parameter is empty. It past contain at least one MountTarget')

    for mt in events['MountTargetIds']:
        logger.info(f'Emptying Security groups for mount point:{mt}')
        vpc_id = efs_client.describe_mount_targets(
            MountTargetId=mt
        )['MountTargets'][0]['VpcId']
        group_id = ec2_client.create_security_group(
            Description='Empty SG for test efs:test:break_security_group:2020-09-21',
            GroupName=f'EmptySG-{mt}-{events["ExecutionId"]}',
            VpcId=vpc_id,
        )['GroupId']

        efs_client.modify_mount_target_security_groups(
            MountTargetId=mt,
            SecurityGroups=[group_id]
        )
