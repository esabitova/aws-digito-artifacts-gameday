from typing import List

import boto3
from boto3 import Session
from .boto3_client_factory import client
import logging
import time

backup_client = boto3.client('backup')
LOG = logging.getLogger(__name__)


def run_backup(session: Session,
               resource_arn: str,
               iam_role_arn: str,
               backup_vault_name: str,
               wait: bool = False,
               wait_timeout: int = 600):
    """
    Issues a backup job
    :param session boto3 client session
    :param resource_arn ARN of resource to be backed up
    :param backup_vault_name Backup Vault Name
    :param iam_role_arn ARN of IAM role used to create the target recovery point
    :param wait True if you want to wait until backup is COMPLETED
    :param wait_timeout timeout in seconds on waiting for backup completion
    """

    LOG.info(f'Starting to back up {resource_arn} into {backup_vault_name}')
    local_backup_client = client('backup', session)
    response = local_backup_client.start_backup_job(
        BackupVaultName=backup_vault_name,
        IamRoleArn=iam_role_arn,
        ResourceArn=resource_arn
    )

    if wait:
        LOG.info(f'Waiting for backup job {response["BackupJobId"]} to complete')
        timeout_timestamp = time.time() + int(wait_timeout)
        status = None
        while time.time() < timeout_timestamp:
            status = get_backup_job_property(session, response['BackupJobId'], 'State')
            if status == "COMPLETED":
                LOG.info(f'Backup job {response["BackupJobId"]} completed')
                break
            time.sleep(5)
        if status != "COMPLETED":
            raise Exception(f'Backup job {response["BackupJobId"]} failed to complete, current status is {status}')
    return response['RecoveryPointArn']


def get_recovery_point(session: Session, backup_vault_name: str, resource_type: str):
    """
    Returns first available completed backup job recovery point
    :param session boto3 client session
    :param backup_vault_name Backup Vault Name
    :param resource_type Resource type (EFS, EC2, etc)
    """
    local_backup_client = client('backup', session)
    response = local_backup_client.list_recovery_points_by_backup_vault(
        BackupVaultName=backup_vault_name,
        ByResourceType=resource_type
    )
    if len(response['RecoveryPoints']) > 0:
        for recovery_point in response['RecoveryPoints']:
            if recovery_point['Status'] == 'COMPLETED':
                return recovery_point['RecoveryPointArn']
    LOG.info(f'No recovery points found for {resource_type} in {backup_vault_name}')
    raise Exception(f'No recovery points found for {resource_type} in {backup_vault_name}')


def get_recovery_points(session: Session, backup_vault_name: str, resource_type: str = None, resource_arn: str = None):
    """
    Returns all backup job recovery points
    :param session boto3 client session
    :param backup_vault_name Backup Vault Name
    :param resource_type Optional. Resource type (EFS, EC2, etc). Leave empty to list all resource types
    :param resource_arn Optional. Backup resource ARN. Leave empty to list all resource ARNs
    """
    local_backup_client = client('backup', session)
    kwargs = {'BackupVaultName': backup_vault_name}
    if resource_type:
        kwargs['ByResourceType'] = resource_type
    if resource_arn:
        kwargs['ByResourceArn'] = resource_arn
    response = local_backup_client.list_recovery_points_by_backup_vault(**kwargs)
    if len(response['RecoveryPoints']) < 0:
        LOG.info(f'No recovery points found for resource_type:{resource_type} '
                 f'resource_arn:{resource_arn} in {backup_vault_name}')
    return response['RecoveryPoints']


def get_backup_job_property(session: Session, backup_job_id: str, path: str):
    """
    Returns backup job description property value
    :param session boto3 client session
    :param backup_job_id Backup job id
    :param path Path to the property in backup job description
    """
    local_backup_client = client('backup', session)
    response = local_backup_client.describe_backup_job(BackupJobId=backup_job_id)
    return __get_property(response, path)


def get_restore_job_property(restore_job_id: str, path: str):
    """
    Returns restore job description property value
    :param restore_job_id Restore job id
    :param path Path to the property in restore job description
    """
    response = backup_client.describe_restore_job(RestoreJobId=restore_job_id)
    return __get_property(response, path)


def delete_recovery_point(session: Session, recovery_point_arn: str, backup_vault_name: str,
                          wait: bool = False,
                          wait_timeout: int = 600):
    """
    Returns restore job description property value
    :param session boto3 client session
    :param recovery_point_arn recovery job arn
    :param backup_vault_name backup vault name
    :param wait True if you want to wait until backup is COMPLETED
    :param wait_timeout timeout in seconds on waiting for backup completion
    """
    local_backup_client = client('backup', session)
    LOG.info(f'Recovery point {recovery_point_arn.split(":")[-1]} is deleting')
    local_backup_client.delete_recovery_point(
        BackupVaultName=backup_vault_name,
        RecoveryPointArn=recovery_point_arn
    )
    if wait:
        timeout_timestamp = time.time() + int(wait_timeout)
        while time.time() < timeout_timestamp:
            try:
                local_backup_client.describe_recovery_point(
                    BackupVaultName=backup_vault_name,
                    RecoveryPointArn=recovery_point_arn
                )
                time.sleep(5)
            except local_backup_client.exceptions.ResourceNotFoundException:
                LOG.info(f'Recovery point {recovery_point_arn.split(":")[-1]} successfully removed')
                break


def __get_property(response: dict, path: str) -> str:
    properties: List = path.split('.')
    result = response
    for prop in properties:
        result = result[prop]
    return str(result)
