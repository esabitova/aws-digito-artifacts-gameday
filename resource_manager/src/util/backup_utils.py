from typing import List

import boto3
import logging

backup_client = boto3.client('backup')
LOG = logging.getLogger(__name__)


def run_backup(resource_arn: str, iam_role_arn: str, backup_vault_name: str):
    """
    Issues a backup job
    :param resource_arn ARN of resource to be backed up
    :param backup_vault_name Backup Vault Name
    :param iam_role_arn ARN of IAM role used to create the target recovery point
    """

    LOG.info(f'Starting to back up {resource_arn} into {backup_vault_name}')
    response = backup_client.start_backup_job(
        BackupVaultName=backup_vault_name,
        IamRoleArn=iam_role_arn,
        ResourceArn=resource_arn
    )
    return response['RecoveryPointArn']


def get_recovery_point(backup_vault_name: str, resource_type: str):
    """
    Returns first available complete backup job recovery point
    :param backup_vault_name Backup Vault Name
    :param resource_type Resource type (EFS, EC2, etc)
    """
    response = backup_client.list_recovery_points_by_backup_vault(
        BackupVaultName=backup_vault_name, ByResourceType=resource_type
    )
    if len(response['RecoveryPoints']) > 0:
        for recovery_point in response['RecoveryPoints']:
            if recovery_point['Status'] == 'COMPLETED':
                return recovery_point['RecoveryPointArn']
    LOG.info(f'No recovery points found for {resource_type} in {backup_vault_name}')
    raise Exception(f'No recovery points found for {resource_type} in {backup_vault_name}')


def get_backup_job_property(backup_job_id: str, path: str):
    """
    Returns backup job description property value
    :param backup_job_id Backup job id
    :param path Path to the property in backup job description
    """
    response = backup_client.describe_backup_job(BackupJobId=backup_job_id)
    return __get_property(response, path)


def get_restore_job_property(restore_job_id: str, path: str):
    """
    Returns restore job description property value
    :param restore_job_id Restore job id
    :param path Path to the property in restore job description
    """
    response = backup_client.describe_restore_job(RestoreJobId=restore_job_id)
    return __get_property(response, path)


def __get_property(response: dict, path: str) -> str:
    properties: List = path.split('.')
    result = response
    for prop in properties:
        result = result[prop]
    return str(result)
