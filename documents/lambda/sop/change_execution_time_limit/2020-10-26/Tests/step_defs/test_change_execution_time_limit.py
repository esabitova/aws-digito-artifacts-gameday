# coding=utf-8
"""SSM automation document for changing Lambda execution time limit."""

from pytest_bdd import (
    scenario,
    when,
    parsers,
    given
)

from resource_manager.src.util import lambda_utils as lambda_utils
from resource_manager.src.util.common_test_utils import generate_different_str_value_by_ranges, \
    put_to_ssm_test_cache, extract_param_value


@scenario('../features/change_execution_time_limit.feature',
          'Create AWS resources using CloudFormation template and execute SSM automation document for changing execution time limit of Lambda')
def test_change_execution_time_limit():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@given(parsers.parse('cache value of "{target_property}" as "{cache_property}" "{step_key}" SSM automation execution'
                     '\n{input_parameters}'))
def cache_lambda_value_before_ssm(resource_manager, ssm_test_cache, target_property, cache_property, step_key,
                                  input_parameters):
    populate_cache(cache_property, input_parameters, resource_manager, ssm_test_cache, step_key, target_property)


@given(parsers.parse('generate different value of "{target_property}" than "{old_property}" as '
                     '"{new_property}" "{step_key}" SSM automation execution'
                     '\n{input_parameters}'))
def generate_different_value(resource_manager, ssm_test_cache, target_property, old_property, new_property,
                             step_key, input_parameters):
    from_range = 0
    to_range = 900
    new_value = generate_different_str_value_by_ranges(input_parameters, old_property, resource_manager, ssm_test_cache,
                                                       from_range, to_range)
    put_to_ssm_test_cache(ssm_test_cache, step_key, new_property, new_value)


@when(parsers.parse('cache value of "{target_property}" as "{cache_property}" "{step_key}" SSM automation execution'
                    '\n{input_parameters}'))
def cache_lambda_value_after_ssm(resource_manager, ssm_test_cache, target_property, cache_property, step_key,
                                 input_parameters):
    populate_cache(cache_property, input_parameters, resource_manager, ssm_test_cache, step_key, target_property)


def populate_cache(cache_property, input_parameters, resource_manager, ssm_test_cache, step_key, target_property):
    lambda_arn = extract_param_value(input_parameters, 'LambdaArn', resource_manager, ssm_test_cache)
    target_property_value = lambda_utils.get_function_configuration_property(lambda_arn, target_property)
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, target_property_value)
