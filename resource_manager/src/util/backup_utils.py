import boto3
from botocore.exceptions import ClientError
from .boto3_client_factory import client
import logging
import time

logger = logging.getLogger(__name__)


def run_backup(session: boto3.Session,
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

    logger.info(f'Starting to back up {resource_arn} into {backup_vault_name}')
    backup_client = client('backup', session)
    response = backup_client.start_backup_job(
        BackupVaultName=backup_vault_name,
        IamRoleArn=iam_role_arn,
        ResourceArn=resource_arn
    )

    if wait:
        logger.info(f'Waiting for backup job {response["BackupJobId"]} to complete')
        timeout_timestamp = time.time() + int(wait_timeout)
        status = None
        while time.time() < timeout_timestamp:
            status = backup_client.describe_backup_job(BackupJobId=response['BackupJobId']).get('State')
            if status == "COMPLETED":
                logger.info(f'Backup job {response["BackupJobId"]} completed')
                break
            time.sleep(5)
        if status != "COMPLETED":
            raise AssertionError(f'Backup job {response["BackupJobId"]} failed to complete, current status is {status}')
    return response['RecoveryPointArn']


def get_recovery_point(session: boto3.Session, backup_vault_name: str, resource_type: str):
    """
    Returns first available completed backup job recovery point
    :param session boto3 client session
    :param backup_vault_name Backup Vault Name
    :param resource_type Resource type (EFS, EC2, etc)
    """
    backup_client = client('backup', session)
    response = backup_client.list_recovery_points_by_backup_vault(
        BackupVaultName=backup_vault_name,
        ByResourceType=resource_type
    )
    if response['RecoveryPoints']:
        for recovery_point in response['RecoveryPoints']:
            if recovery_point['Status'] == 'COMPLETED':
                return recovery_point['RecoveryPointArn']
    logger.info(f'No recovery points found for {resource_type} in {backup_vault_name}')
    raise AttributeError(
        f'No recovery points found for {resource_type} in {backup_vault_name}'
    )


def get_recovery_points(session: boto3.Session, backup_vault_name: str, resource_type: str = None,
                        resource_arn: str = None):
    """
    Returns all backup job recovery points
    :param session boto3 client session
    :param backup_vault_name Backup Vault Name
    :param resource_type Optional. Resource type (EFS, EC2, etc). Leave empty to list all resource types
    :param resource_arn Optional. Backup resource ARN. Leave empty to list all resource ARNs
    """
    backup_client = client('backup', session)
    kwargs = {'BackupVaultName': backup_vault_name}
    if resource_type:
        kwargs['ByResourceType'] = resource_type
    if resource_arn:
        kwargs['ByResourceArn'] = resource_arn
    response = backup_client.list_recovery_points_by_backup_vault(**kwargs)
    if not response['RecoveryPoints']:
        logger.info(f'No recovery points found for resource_type:{resource_type} '
                    f'resource_arn:{resource_arn} in {backup_vault_name}')
    return response['RecoveryPoints']


def delete_recovery_point(session: boto3.Session, recovery_point_arn: str, backup_vault_name: str,
                          wait: bool = False,
                          wait_timeout: int = 600,
                          region: str = None):
    """
    Deletes recovery point by its ARN
    :param session boto3 client session
    :param recovery_point_arn recovery point arn
    :param backup_vault_name backup vault name
    :param wait True if you want to wait until delete is completed
    :param wait_timeout timeout in seconds on waiting for delete completion
    :param region Name of region to look for backup vault, if None, use current region
    """
    logger.info(f'Recovery point {recovery_point_arn.split(":")[-1]} is deleting')
    if region:
        backup_client = session.client('backup', region_name=region)
    else:
        backup_client = client('backup', session)
    backup_client.delete_recovery_point(
        BackupVaultName=backup_vault_name,
        RecoveryPointArn=recovery_point_arn
    )
    if wait:
        is_successful = False
        timeout_timestamp = time.time() + int(wait_timeout)
        while time.time() < timeout_timestamp:
            try:
                backup_client.describe_recovery_point(
                    BackupVaultName=backup_vault_name,
                    RecoveryPointArn=recovery_point_arn
                )
                time.sleep(5)
            except ClientError:
                logger.info(f'Recovery point {recovery_point_arn.split(":")[-1]} successfully removed')
                is_successful = True
                break
        if not is_successful:
            raise TimeoutError(f'Recovery point \'{recovery_point_arn.split(":")[-1]}\' wasn\'t removed during timeout')
        else:
            return True


def delete_backup_vault(session: boto3.Session, backup_vault_name: str, region: str = None):
    """
    Deletes backup vault by its name in a specified region
    :param session boto3 client session
    :param backup_vault_name backup vault name
    :param region Name of region to look for backup vault, if None, use current region
    """
    logger.info(f'Backup vault {backup_vault_name} is deleting')

    if region:
        backup_client = session.client('backup', region_name=region)
    else:
        backup_client = client('backup', session)

    response = backup_client.delete_backup_vault(
        BackupVaultName=backup_vault_name
    )

    return response


def issue_a_backup_job_and_immediately_abort_it(
    session: boto3.Session,
    backed_resource_arn: str,
    iam_role_arn: str,
    backup_vault_name: str,
):
    """
    Issues a backup job for specified resource and immediately cancels it
    :param session boto3 client session
    :param backed_resource_arn ARN of resource to be backed up
    :param iam_role_arn ARN of IAM role used to create the target recovery point
    :param backup_vault_name Backup Vault Name
    """
    backup_client = session.client('backup')
    logger.info(f'Issuing a backup job for [{backed_resource_arn}] in [{backup_vault_name}]')
    response = backup_client.start_backup_job(
        BackupVaultName=backup_vault_name,
        IamRoleArn=iam_role_arn,
        ResourceArn=backed_resource_arn
    )
    backup_job_id = response["BackupJobId"]
    logger.info(f'Issuing a cancel to a backup job [{backup_job_id}]')
    backup_client.stop_backup_job(
        BackupJobId=backup_job_id
    )
