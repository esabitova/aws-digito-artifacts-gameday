import boto3
import logging
import time

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def copy_backup_in_region(events, context):
    required_params = [
        'IamRoleArn',
        'RecoveryPointArn',
        'IdempotencyToken',
        'DestinationBackupVaultArn',
        'SourceBackupVaultName'
    ]
    for key in required_params:
        if key not in events:
            raise KeyError(f'Requires {key} in events')

    backup_client = boto3.client('backup')
    logger.info(f'Running Copy backup with the following args: {events}')
    response = backup_client.start_copy_job(
        RecoveryPointArn=events['RecoveryPointArn'],
        SourceBackupVaultName=events['SourceBackupVaultName'],
        DestinationBackupVaultArn=events['DestinationBackupVaultArn'],
        IamRoleArn=events['IamRoleArn'],
        IdempotencyToken=events['IdempotencyToken']
    )
    return {
        'CopyJobId': response.get('CopyJobId')
    }


def restore_backup_in_region(events, context):
    required_params = [
        'IamRoleArn',
        'RecoveryPointArn',
        'IdempotencyToken',
        'Region',
        'Metadata',
        'ResourceType'
    ]
    required_metadata = [
        'file-system-id',
        'Encrypted',
        'PerformanceMode',
        'newFileSystem',
        'CreationToken'
    ]
    for key in required_params:
        if key not in events:
            raise KeyError(f'Requires {key} in events')
    for key in required_metadata:
        if key not in events['Metadata']:
            raise KeyError(f'Requires {key} in events\' Metadata')

    backup_client = boto3.client('backup', region_name=events['Region'])
    logger.info(f'Running Restore with the following args: {events}')
    response = backup_client.start_restore_job(
        RecoveryPointArn=events['RecoveryPointArn'],
        Metadata={
            'file-system-id': events['Metadata']['file-system-id'],
            'Encrypted': events['Metadata']['Encrypted'],
            'PerformanceMode': events['Metadata']['PerformanceMode'],
            'CreationToken': events['Metadata']['CreationToken'],
            'newFileSystem': events['Metadata']['newFileSystem']
        },
        IamRoleArn=events['IamRoleArn'],
        IdempotencyToken=events['IdempotencyToken'],
        ResourceType=events['ResourceType'],
    )
    return {
        'RestoreJobId': response.get('RestoreJobId')
    }


def wait_restore_job_in_region(events, context):
    required_params = [
        'RestoreJobId',
        'Region',
    ]
    wait_timeout = 3600
    result = {}
    for key in required_params:
        if key not in events:
            raise KeyError(f'Requires {key} in events')

    if 'WaitTimeout' in events:
        wait_timeout = events['WaitTimeout']
    backup_client = boto3.client('backup', region_name=events['Region'])
    logger.info(f"Waiting for restore job id {events['RestoreJobId']} in region: {events['Region']}")

    timeout_timestamp = time.time() + int(wait_timeout)
    while time.time() < timeout_timestamp:
        response = backup_client.describe_restore_job(
            RestoreJobId=events['RestoreJobId']
        )
        if response.get('Status') == 'COMPLETED':
            result = {
                'RestoreJobId': response.get('RestoreJobId'),
                'CreatedResourceArn': response.get('CreatedResourceArn')
            }
            break
        elif response.get('Status') in ['ABORTED', 'FAILED']:
            raise AssertionError(f"Restore job resulted with {response.get('Status')} status")
        time.sleep(20)
    if not result:
        raise TimeoutError(f"Restore job couldn't be completed within {wait_timeout} seconds")
    return result
