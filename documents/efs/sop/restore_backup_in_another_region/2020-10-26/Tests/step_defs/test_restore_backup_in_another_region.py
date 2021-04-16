# coding=utf-8
"""SSM automation document to restore backup in another region"""

from pytest_bdd import (
    scenario,
    given,
    then,
    parsers
)
import logging
import resource_manager.src.util.backup_utils as backup_utils

from resource_manager.src.util.common_test_utils import extract_param_value, put_to_ssm_test_cache
from resource_manager.src.util.iam_utils import get_role_by_name
from resource_manager.src.util.efs_utils import describe_filesystem

LOG = logging.getLogger(__name__)


@scenario('../features/restore_backup_in_another_region.feature',
          'Restore backup in another region')
def test_restore_backup():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@given(parsers.parse('cache number of recovery points as "{cache_property}" "{step_key}" SSM '
                     'automation execution'
                     '\n{input_parameters}'))
@then(parsers.parse('cache number of recovery points as "{cache_property}" "{step_key}" SSM '
                    'automation execution'
                    '\n{input_parameters}'))
def cache_number_of_recovery_points(
        resource_manager, boto3_session, ssm_test_cache, cache_property, step_key, input_parameters):
    backup_vault_name = extract_param_value(input_parameters, "BackupVaultName", resource_manager, ssm_test_cache)
    efs_id = extract_param_value(input_parameters, 'FileSystemID', resource_manager, ssm_test_cache)
    efs_arn = describe_filesystem(boto3_session, efs_id)['FileSystems'][0]['FileSystemArn']
    recovery_points = backup_utils.get_recovery_points(boto3_session, backup_vault_name, resource_arn=efs_arn)
    LOG.info(f'{len(recovery_points)} recovery points found for efs_id:{efs_id} '
             f'in {backup_vault_name} {step_key} SSM')
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, len(recovery_points))


@given(parsers.parse('cache recovery point arn as "{cache_property}" '
                     '"{step_key}" SSM automation execution\n{input_parameters}'))
def cache_recovery_point_arn(resource_manager, boto3_session, ssm_test_cache,
                             cache_property, step_key, input_parameters):
    efs_id = extract_param_value(input_parameters, 'FileSystemID', resource_manager, ssm_test_cache)
    backup_vault_name = extract_param_value(input_parameters, 'BackupVaultName', resource_manager, ssm_test_cache)
    default_iam_role_arn = get_role_by_name(boto3_session, "AWSBackupDefaultServiceRole")['Role']['Arn']
    efs_arn = describe_filesystem(boto3_session, efs_id)['FileSystems'][0]['FileSystemArn']
    recovery_point_arn = backup_utils.run_backup(boto3_session,
                                                 efs_arn,
                                                 default_iam_role_arn,
                                                 backup_vault_name,
                                                 wait=True)
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, recovery_point_arn)


@then(parsers.parse('tear down created recovery points and jobs\n{input_parameters}'))
def tear_down(resource_manager, boto3_session, ssm_test_cache, input_parameters):
    recovery_point_arn = extract_param_value(input_parameters, 'RecoveryPointArn', resource_manager, ssm_test_cache)
    backup_vault_name = extract_param_value(input_parameters, 'BackupVaultName', resource_manager, ssm_test_cache)
    backup_utils.delete_recovery_point(boto3_session, recovery_point_arn, backup_vault_name, wait=True)
