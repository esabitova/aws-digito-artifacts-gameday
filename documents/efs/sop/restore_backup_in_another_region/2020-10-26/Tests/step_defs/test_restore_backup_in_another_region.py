# coding=utf-8
"""SSM automation document to restore backup in another region"""

from pytest_bdd import (
    scenario,
    given,
    then,
    when,
    parsers
)
import logging
import resource_manager.src.util.backup_utils as backup_utils

from resource_manager.src.util.common_test_utils import extract_param_value, put_to_ssm_test_cache
from resource_manager.src.util.iam_utils import get_role_by_name
from resource_manager.src.util.efs_utils import describe_filesystem, delete_filesystem

logger = logging.getLogger(__name__)


@scenario('../features/restore_backup_in_another_region.feature',
          'Restore backup in another region')
def test_restore_backup():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


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


@given(parsers.parse('cache different region name as "{cache_property}" "{step_key}" '
                     'SSM automation execution'))
@when(parsers.parse('cache different region name as "{cache_property}" "{step_key}" '
                    'SSM automation execution'))
def cache_different_region(boto3_session, ssm_test_cache,
                           cache_property, step_key):

    source_region = boto3_session.region_name
    available_region_list = boto3_session.get_available_regions('efs')
    available_region_list.remove(source_region)
    # remove regions not supporting cross-region backups
    available_region_list.remove('eu-south-1')
    available_region_list.remove('af-south-1')
    available_region_list.remove('ap-east-1')
    available_region_list.remove('me-south-1')
    logger.info(f'Available region list: {available_region_list}')
    # choose the first region from a location where source EFS volume was created
    # if location contains only one region and it contains source EFS volume, choose the first one from other location
    destination_region = available_region_list[0]
    for region in available_region_list:
        if region.startswith(source_region.split('-')[0]):
            destination_region = region
            break
    logger.info(f'Caching new region for EFS: {destination_region}')
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, destination_region)


@then(parsers.parse('tear down created recovery point\n{input_parameters}'))
def teardown_recovery_point(resource_manager, boto3_session, ssm_test_cache, input_parameters):
    logger.info(f"ssm_test_cache:{ssm_test_cache}")
    recovery_point_arn = extract_param_value(input_parameters, 'RecoveryPointArn', resource_manager, ssm_test_cache)
    region = extract_param_value(input_parameters, 'RegionName', resource_manager, ssm_test_cache)
    backup_vault_name = extract_param_value(input_parameters, 'BackupVaultName', resource_manager, ssm_test_cache)
    backup_utils.delete_recovery_point(boto3_session, recovery_point_arn, backup_vault_name, wait=True, region=region)


@then(parsers.parse('tear down backup vault\n{input_parameters}'))
def teardown_backup_vault(resource_manager, boto3_session, ssm_test_cache, input_parameters):
    backup_vault_arn = extract_param_value(input_parameters, 'BackupVaultArn', resource_manager, ssm_test_cache)
    region = extract_param_value(input_parameters, 'RegionName', resource_manager, ssm_test_cache)
    backup_vault_name = backup_vault_arn.split(':')[-1]
    backup_utils.delete_backup_vault(boto3_session, backup_vault_name, region=region)


@then(parsers.parse('tear down filesystem by ARN\n{input_parameters}'))
def teardown_fs_by_arn(resource_manager, boto3_session, ssm_test_cache, input_parameters):
    fs_arn = extract_param_value(input_parameters, 'FileSystemARN', resource_manager, ssm_test_cache)
    fs_id = fs_arn.split(':')[-1].split('/')[-1]
    delete_filesystem(boto3_session, fs_id)
