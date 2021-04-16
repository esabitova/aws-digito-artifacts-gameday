from pytest_bdd import (
    parsers, when, given, then
)
import jsonpath_ng
import logging
from resource_manager.src.util.param_utils import parse_param_values_from_table
from resource_manager.src.util.common_test_utils import extract_param_value, put_to_ssm_test_cache
import resource_manager.src.util.backup_utils as backup_utils
from resource_manager.src.util.efs_utils import describe_filesystem

logger = logging.getLogger(__name__)


@when(parsers.parse('cache restore job property "{target_property}" as "{cache_property}" '
                    '"{step_key}" SSM automation execution\n{input_parameters}'))
def cache_backup_value(cfn_output_params, ssm_test_cache, boto3_session, json_path, cache_property, step_key,
                       input_parameters):
    restore_job_id = parse_param_values_from_table(input_parameters, {
        'cache': ssm_test_cache,
        'cfn-output': cfn_output_params})[0].get('RestoreJobId')
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
