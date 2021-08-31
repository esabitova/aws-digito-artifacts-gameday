import logging
import time
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError
from dateutil import parser

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def start_time(events, context):
    return datetime.now(timezone.utc).isoformat()


def recovery_time(events, context):
    return (datetime.now(timezone.utc) - parser.parse(events['StartTime'])).seconds


def create_empty_security_group(events, context):
    required_params = [
        'VpcId',
        'ExecutionId'
    ]

    for key in required_params:
        if key not in events:
            raise KeyError(f'Requires {key} in events')

    ec2_client = boto3.client('ec2')

    group_id = ec2_client.create_security_group(
        Description=f'Empty SG for executionID {events["ExecutionId"]}',
        GroupName=f'EmptySG-{events["ExecutionId"]}',
        VpcId=events['VpcId'],
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
    return {'EmptySecurityGroupId': group_id}


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


def raise_exception(events, context):
    """
    Raises AssertionError exception with defined error message
    You can pass additional arguments to run python format() on the message.
    Example:

    ErrorMessage: "test {test1} {test2}"
    test1: "replaced1"
    test2: "replaced2"

    will render in
    `test replaced1 replaced2`


    :param events: dict with the following keys:
        * ErrorMessage: error message to return, you can add placeholders in {} and replace them with other parameters
        * any_key: will replace placeholder {any_key} in ErrorMessage
    :param context:
    :return: None
    """
    required_params = [
        'ErrorMessage'
    ]

    for key in required_params:
        if key not in events:
            raise KeyError(f'Requires {key} in events')

    format_dict = {k: v for k, v in events.items() if k != 'ErrorMessage'}
    raise AssertionError(events['ErrorMessage'].format(**format_dict))
