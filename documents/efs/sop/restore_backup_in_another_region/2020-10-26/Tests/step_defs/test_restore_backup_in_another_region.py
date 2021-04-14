# coding=utf-8
"""SSM automation document to restore backup in another region"""

from pytest_bdd import (
    scenario,
    given,
    parsers
)

from resource_manager.src.util.backup_utils import get_recovery_point, run_backup
from resource_manager.src.util.common_test_utils import extract_param_value, put_to_ssm_test_cache
from resource_manager.src.util.iam_utils import get_role_by_name
from resource_manager.src.util.efs_utils import describe_filesystem


@scenario('../features/restore_backup_in_another_region.feature',
          'Restore backup in another region')
def test_restore_backup():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@given(parsers.parse('cache recovery point arn as "{cache_property}"\n{input_parameters}'))
def cache_recovery_point_arn(resource_manager, boto3_session, ssm_test_cache, cache_property, input_parameters):
    efs_id = extract_param_value(input_parameters, 'FileSystemID', resource_manager, ssm_test_cache)
    backup_vault_name = extract_param_value(input_parameters, 'BackupVaultName', resource_manager, ssm_test_cache)
    default_iam_role_arn = get_role_by_name(boto3_session, "AWSBackupDefaultServiceRole")['Role']['Arn']
    efs_arn = describe_filesystem(boto3_session, efs_id)['FileSystems'][0]['FileSystemArn']
    run_backup(efs_arn, default_iam_role_arn, backup_vault_name)
    recovery_point_arn = get_recovery_point(backup_vault_name, 'EFS')
    put_to_ssm_test_cache(ssm_test_cache, 'before', cache_property, recovery_point_arn)
