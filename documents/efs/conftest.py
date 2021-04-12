from pytest_bdd import (
    parsers, when,
)

from resource_manager.src.util.param_utils import parse_param_values_from_table
from resource_manager.src.util.backup_utils import get_restore_job_property
from resource_manager.src.util.common_test_utils import put_to_ssm_test_cache


@when(parsers.parse('cache restore job property of "{target_property}" as "{cache_property}" '
                    '"{step_key}" SSM automation execution\n{input_parameters}'))
def cache_backup_value(cfn_output_params, ssm_test_cache, target_property, cache_property, step_key,
                       input_parameters):
    restore_job_id = parse_param_values_from_table(input_parameters, {
        'cache': ssm_test_cache,
        'cfn-output': cfn_output_params})[0].get('RestoreJobId')
    target_property_value = get_restore_job_property(restore_job_id, target_property)
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, target_property_value)
