import boto3
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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
    return response.get('RestoreJobId')
