import jsonpath_ng
import logging
import uuid
from pytest_bdd import (
    parsers, when, given, then
)
from botocore.exceptions import ClientError

from resource_manager.src.util import backup_utils, ec2_utils
from resource_manager.src.util.param_utils import parse_param_values_from_table, parse_param_value
from resource_manager.src.util.common_test_utils import extract_param_value, put_to_ssm_test_cache
from resource_manager.src.util.efs_utils import describe_filesystem

logger = logging.getLogger(__name__)


@given(parsers.parse('cache filesystem property "{json_path}" as "{cache_property}" "{step_key}" SSM automation '
                     'execution\n{input_parameters}'))
@when(parsers.parse('cache filesystem property "{json_path}" as "{cache_property}" "{step_key}" SSM automation '
                    'execution\n{input_parameters}'))
@then(parsers.parse('cache filesystem property "{json_path}" as "{cache_property}" "{step_key}" SSM automation '
                    'execution\n{input_parameters}'))
def cache_filesystem_property(resource_pool, ssm_test_cache, boto3_session, json_path, cache_property, step_key,
                              input_parameters):
    filesystem_id = extract_param_value(input_parameters, 'FileSystemID', resource_pool, ssm_test_cache)
    response = describe_filesystem(boto3_session, filesystem_id)['FileSystems'][0]
    target_value = jsonpath_ng.parse(json_path).find(response)[0].value
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, target_value)


@when(parsers.parse('cache restore job property "{json_path}" as "{cache_property}" '
                    '"{step_key}" SSM automation execution\n{input_parameters}'))
def cache_backup_value(cfn_output_params, resource_pool, ssm_test_cache, boto3_session, json_path, cache_property,
                       step_key, input_parameters):
    restore_job_id = parse_param_values_from_table(input_parameters, {
        'cache': ssm_test_cache,
        'cfn-output': cfn_output_params})[0].get('RestoreJobId')
    region = None
    try:
        region = extract_param_value(input_parameters, 'RegionName', resource_pool, ssm_test_cache)
    except KeyError:
        pass
    if restore_job_id:
        if region:
            backup_client = boto3_session.client('backup', region_name=region)
        else:
            backup_client = boto3_session.client('backup')
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
        resource_pool, boto3_session, ssm_test_cache, cache_property, step_key, input_parameters):
    backup_vault_name = extract_param_value(input_parameters, "BackupVaultName", resource_pool, ssm_test_cache)
    efs_id = extract_param_value(input_parameters, 'FileSystemID', resource_pool, ssm_test_cache)
    efs_arn = describe_filesystem(boto3_session, efs_id)['FileSystems'][0]['FileSystemArn']
    recovery_points = backup_utils.get_recovery_points(boto3_session, backup_vault_name, resource_arn=efs_arn)
    logger.info(f'{len(recovery_points)} recovery points found for efs_id:{efs_id} '
                f'in {backup_vault_name} {step_key} SSM')
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, len(recovery_points))


@given(parsers.parse('create a backup vault in region as "{cache_property}" "{step_key}" SSM automation execution'
                     '\n{input_parameters}'))
def create_backup_vault_in_region(
        resource_pool, boto3_session, ssm_test_cache, cache_property, step_key, input_parameters):
    backup_vault_name = f"dest-{uuid.uuid4()}"
    region = extract_param_value(input_parameters, 'RegionName', resource_pool, ssm_test_cache)
    backup_client = boto3_session.client('backup', region_name=region)
    backup_vault_arn = backup_client.create_backup_vault(BackupVaultName=backup_vault_name)['BackupVaultArn']
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, backup_vault_arn)


@then(parsers.parse('assert EFS fs exists\n{input_parameters}'))
def efs_fs_exists(resource_pool, boto3_session, ssm_test_cache, input_parameters):
    efs_id = extract_param_value(input_parameters, 'FileSystemARN', resource_pool, ssm_test_cache). \
        split(':')[-1].split('/')[-1]
    region = None
    try:
        region = extract_param_value(input_parameters, 'RegionName', resource_pool, ssm_test_cache)
    except KeyError:
        pass
    try:
        describe_filesystem(boto3_session, efs_id, region=region)['FileSystems'][0]['FileSystemArn']
    except ClientError:
        raise AssertionError(f'FileSystem with ID {efs_id} doesn\'t exist after restore')


@then(parsers.parse('tear down created recovery point\n{input_parameters}'))
def teardown_recovery_point(resource_pool, boto3_session, ssm_test_cache, input_parameters):
    logger.info(f"ssm_test_cache:{ssm_test_cache}")
    recovery_point_arn = extract_param_value(input_parameters, 'RecoveryPointArn', resource_pool, ssm_test_cache)
    region = None
    backup_vault_name = ""
    try:
        region = extract_param_value(input_parameters, 'RegionName', resource_pool, ssm_test_cache)
    except KeyError:
        pass
    try:
        backup_vault_name = extract_param_value(input_parameters, 'BackupVaultName', resource_pool, ssm_test_cache)
    except KeyError:
        pass
    try:
        backup_vault_arn = extract_param_value(input_parameters, 'BackupVaultArn', resource_pool, ssm_test_cache)
        backup_vault_name = backup_vault_arn.split(':')[-1]
    except KeyError:
        pass
    if not backup_vault_name:
        raise AssertionError('Backup vault name is not specified for a recovery point tear down')
    backup_utils.delete_recovery_point(boto3_session, recovery_point_arn, backup_vault_name, wait=True, region=region)


@when(parsers.parse('ec2 {ec2_instance_ref} is rebooted'))
def reboot_instance(ec2_instance_ref, cfn_output_params, ssm_test_cache, boto3_session):
    ec2_instance = parse_param_value(ec2_instance_ref, {'cfn-output': cfn_output_params,
                                                        'cache': ssm_test_cache})
    ec2_utils.reboot_instance(boto3_session, ec2_instance)
