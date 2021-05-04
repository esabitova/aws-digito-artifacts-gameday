# coding=utf-8

import resource_manager.src.util.efs_utils as efs_utils

from pytest_bdd import (
    scenario,
    then
)
from botocore.exceptions import ClientError
from pytest_bdd.parsers import parse
from resource_manager.src.util.common_test_utils import extract_param_value


@scenario('../features/create_backup.feature',
          'Create AWS resources using CloudFormation template and execute SSM automation document to '
          'create backup of EFS')
def test_create_backup():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@then(parse('assert RecoveryPoint fs exists and correct\n{input_parameters}'))
def assert_recovery_point_exists_and_correct(resource_manager, boto3_session, ssm_test_cache, input_parameters):
    recovery_point_arn = extract_param_value(input_parameters, 'RecoveryPointArn', resource_manager, ssm_test_cache)
    backup_vault_name = extract_param_value(input_parameters, 'BackupVaultName', resource_manager, ssm_test_cache)
    fs_id = extract_param_value(input_parameters, 'FileSystemId', resource_manager, ssm_test_cache)
    fs_arn = efs_utils.describe_filesystem(boto3_session, fs_id=fs_id)
    backup_client = boto3_session.client('backup')
    try:
        response = backup_client.describe_recovery_point(
            BackupVaultName=backup_vault_name,
            RecoveryPointArn=recovery_point_arn
        )
    except ClientError:
        raise AssertionError(f'Recovery point {recovery_point_arn} doesn\'t exist '
                             f'for a backup vault {backup_vault_name}')
    assert response['ResourceArn'] == fs_arn['FileSystems'][0]['FileSystemArn']
