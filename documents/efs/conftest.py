from pytest_bdd import (
    parsers, when, given, then
)
import jsonpath_ng
import logging
import uuid
import boto3
from resource_manager.src.util.param_utils import parse_param_values_from_table
from resource_manager.src.util.common_test_utils import extract_param_value, put_to_ssm_test_cache
import resource_manager.src.util.backup_utils as backup_utils
from resource_manager.src.util.efs_utils import describe_filesystem

logger = logging.getLogger(__name__)


@when(parsers.parse('cache restore job property "{json_path}" as "{cache_property}" '
                    '"{step_key}" SSM automation execution\n{input_parameters}'))
def cache_backup_value(cfn_output_params, resource_manager, ssm_test_cache, boto3_session, json_path, cache_property,
                       step_key, input_parameters):
    restore_job_id = parse_param_values_from_table(input_parameters, {
        'cache': ssm_test_cache,
        'cfn-output': cfn_output_params})[0].get('RestoreJobId')
    region = extract_param_value(input_parameters, 'RegionName', resource_manager, ssm_test_cache)
    if region:
        backup_client = boto3.client('backup', region_name=region)
    else:
        backup_client = boto3_session.client('backup')
    if restore_job_id:
        response = backup_client.describe_restore_job(RestoreJobId=restore_job_id)
        target_value = jsonpath_ng.parse(json_path).find(response)[0].value
        put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, target_value)
    else:
        raise AssertionError('RestoreJobId was not provided for "cache restore property" step')


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
    logger.info(f'{len(recovery_points)} recovery points found for efs_id:{efs_id} '
                f'in {backup_vault_name} {step_key} SSM')
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, len(recovery_points))


@given(parsers.parse('create a backup vault in region as "{cache_property}" "{step_key}" SSM automation execution'
                     '\n{input_parameters}'))
def create_backup_vault_in_region(
        resource_manager, boto3_session, ssm_test_cache, cache_property, step_key, input_parameters):
    backup_vault_name = f"dest-{uuid.uuid4()}"
    region = extract_param_value(input_parameters, 'RegionName', resource_manager, ssm_test_cache)
    backup_client = boto3_session.client('backup', region_name=region)
    backup_vault_arn = backup_client.create_backup_vault(BackupVaultName=backup_vault_name)['BackupVaultArn']
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, backup_vault_arn)


@then(parsers.parse('assert EFS fs exists\n{input_parameters}'))
def efs_fs_exists(resource_manager, boto3_session, ssm_test_cache, input_parameters):
    efs_id = extract_param_value(input_parameters, 'FileSystemARN', resource_manager, ssm_test_cache).\
        split(':')[-1].split('/')[-1]
    try:
        describe_filesystem(boto3_session, efs_id)['FileSystems'][0]['FileSystemArn']
    except boto3_session.client('backup').exceptions.FileSystemNotFound:
        raise AssertionError(f'FileSystem with ID {efs_id} doesn\'t exist after restore')
