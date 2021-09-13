import boto3
import logging
from datetime import datetime, timezone
import time

from botocore.exceptions import ClientError
from dateutil import parser

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def start_time(events, context):
    return datetime.now(timezone.utc).isoformat()


def recovery_time(events, context):
    return (datetime.now(timezone.utc) - parser.parse(events['StartTime'])).seconds


def create_empty_security_group(events: dict, context: dict) -> dict:
    """
    Creates a empty security group in provided VPC
    The name of this SG contains Execution Id of the SSM execution
    :param events: The dictionary that supposed to have the following keys:
        * `VpcId` - The vpc id to create SG into
        * `ExecutionId` - The execution id of SSM
        * `Tag` - a value of `Digito` tag to assign
    :param context:
    :return: Dict with two keys:
        * EmptySecurityGroupId - string wih SG id, you can use it as String parameter in SSM
        * EmptySecurityGroupId - one element list wih SG id, you can use it as StringList parameter in SSM
    """
    required_params = [
        'VpcId',
        'ExecutionId',
        'Tag'
    ]

    for key in required_params:
        if key not in events:
            raise KeyError(f'Requires {key} in events')

    ec2_client = boto3.client('ec2')

    group_id = ec2_client.create_security_group(
        Description=f'Empty SG for executionID {events["ExecutionId"]}',
        GroupName=f'EmptySG-{events["ExecutionId"]}',
        VpcId=events['VpcId'],
        TagSpecifications=[
            {
                'ResourceType': 'security-group',
                'Tags': [
                    {
                        'Key': 'Digito',
                        'Value': events['Tag']
                    },
                ]
            }
        ]
    )['GroupId']

    result = ec2_client.revoke_security_group_egress(
        GroupId=group_id,
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
    if not result['Return']:
        remove_empty_security_group({'EmptySecurityGroupId': group_id}, context)
        raise ClientError(
            error_response={
                "Error":
                {
                    "Code": "CouldNotRevoke",
                    "Message": f"Could not revoke egress from sg: {group_id}"
                }
            },
            operation_name='RevokeSecurityGroupEgress'
        )
    return {'EmptySecurityGroupId': group_id, 'EmptySecurityGroupIdList': [group_id]}


def remove_empty_security_group(events, context):
    required_params = [
        'EmptySecurityGroupId'
    ]

    for key in required_params:
        if key not in events:
            raise KeyError(f'Requires {key} in events')

    time_to_wait = 1800
    ec2_client = boto3.client('ec2')
    if 'Timeout' in events:
        time_to_wait = events['Timeout']
    timeout_timestamp = time.time() + int(time_to_wait)

    while time.time() < timeout_timestamp:
        try:
            logger.info(f'Deleting empty security group: {events["EmptySecurityGroupId"]}')
            group_list = ec2_client.describe_security_groups(
                Filters=[
                    {
                        'Name': 'group-id',
                        'Values': [
                            events["EmptySecurityGroupId"],
                        ]
                    },
                ]
            )
            if not group_list['SecurityGroups']:
                break
            group_id = group_list['SecurityGroups'][0]['GroupId']
            logger.info(f'Deleting empty security group: {group_id}')
            response = ec2_client.delete_security_group(
                GroupId=group_id
            )
            if response['ResponseMetadata']['HTTPStatusCode'] < 400:
                break
        except ClientError as error:
            if error.response['Error']['Code'] == 'InvalidGroup.NotFound':
                logger.info(f"Empty security group doesn't exist: {events['EmptySecurityGroupId']}")
                break
            elif error.response['Error']['Code'] == 'DependencyViolation' \
                    or error.response['Error']['Code'] == 'RequestLimitExceeded':
                time.sleep(5)
                continue
            else:
                raise error

    if datetime.timestamp(datetime.now()) > timeout_timestamp:
        raise TimeoutError(f'Security group {events["EmptySecurityGroupId"]} couldn\'t '
                           f'be deleted in {time_to_wait} seconds')
