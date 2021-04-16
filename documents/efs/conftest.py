from pytest_bdd import (
    parsers, when,
)

from resource_manager.src.util.param_utils import parse_param_values_from_table


@when(parsers.parse('cache property of "{target_property}" as "{cache_property}" '
                    '"{step_key}" SSM automation execution\n{input_parameters}'))
def cache_backup_value(cfn_output_params, ssm_test_cache, target_property, cache_property, step_key,
                       input_parameters):
    restore_job_id = parse_param_values_from_table(input_parameters, {
        'cache': ssm_test_cache,
        'cfn-output': cfn_output_params})[0].get('RestoreJobId')
    print(restore_job_id)
    print(target_property)
    print(cache_property)
    print(step_key)
