from pytest_bdd import (
    then,
    when,
    given,
    parsers
)

from resource_manager.src.util.common_test_utils import generate_and_cache_different_value_by_property_name
from resource_manager.src.util.common_test_utils import generate_and_cache_different_list_value_by_property_name


@then(parsers.parse('assert "{expected_property}" at "{step_key_for_expected}" '
                    'became equal to "{actual_property}" at "{step_key_for_actual}"'))
def assert_equal(ssm_test_cache, expected_property, step_key_for_expected, actual_property, step_key_for_actual):
    assert ssm_test_cache[step_key_for_expected][expected_property] \
           == ssm_test_cache[step_key_for_actual][actual_property]


@then(parsers.cfparse('assert the difference between "{expected_property}" at "{step_key_for_expected}" '
                      'and "{actual_property}" at "{step_key_for_actual}" became "{expected_difference:int}"',
                      extra_types=dict(int=int)))
def assert_difference(ssm_test_cache, expected_property, step_key_for_expected, actual_property, step_key_for_actual,
                      expected_difference: int):
    assert int(ssm_test_cache[step_key_for_expected][expected_property]) \
           - int(ssm_test_cache[step_key_for_actual][actual_property]) == expected_difference


@then(parsers.parse('assert "{expected_property}" at "{step_key_for_expected}" '
                    'became not equal to "{actual_property}" at "{step_key_for_actual}"'))
def assert_not_equal(ssm_test_cache, expected_property, step_key_for_expected, actual_property, step_key_for_actual):
    assert ssm_test_cache[step_key_for_expected][expected_property] \
           != ssm_test_cache[step_key_for_actual][actual_property]


@then(parsers.parse('assert "{expected_property}" at "{step_key_for_expected}" '
                    'became equal to "{actual_value}"'))
def assert_equal_to_value(ssm_test_cache, expected_property, step_key_for_expected, actual_value):
    assert ssm_test_cache[step_key_for_expected][expected_property] == actual_value


@then(parsers.parse('assert "{expected_property}" at "{step_key_for_expected}" '
                    'less than "{actual_property}" at "{step_key_for_actual}"'))
def assert_less_than(ssm_test_cache, expected_property, step_key_for_expected, actual_property, step_key_for_actual):
    assert ssm_test_cache[step_key_for_expected][expected_property] \
           < ssm_test_cache[step_key_for_actual][actual_property]


@given(parsers.parse('generate different value of "{target_property}" than "{old_property}" from "{from_range}" to'
                     ' "{to_range}" as "{cache_property}" "{cache_key}" SSM automation execution'
                     '\n{input_parameters}'))
@when(parsers.parse('generate different value of "{target_property}" than "{old_property}" from "{from_range}" to'
                    ' "{to_range}" as "{cache_property}" "{cache_key}" SSM automation execution'
                    '\n{input_parameters}'))
def generate_and_cache_different_value_by_property_name_from_expression(resource_pool, ssm_test_cache, old_property,
                                                                        from_range, to_range, cache_property, step_key,
                                                                        input_parameters):
    generate_and_cache_different_value_by_property_name(resource_pool, ssm_test_cache, old_property, from_range,
                                                        to_range, cache_property, step_key, input_parameters)


@given(parsers.parse('generate different list value of "{target_property}" than "{old_property}" from "{input_list}"'
                     ' as "{cache_property}" "{cache_key}" SSM automation execution'
                     '\n{input_parameters}'))
@when(parsers.parse('generate different list value of "{target_property}" than "{old_property}" from "{input_list}"'
                    ' as "{cache_property}" "{cache_key}" SSM automation execution'
                    '\n{input_parameters}'))
def generate_and_cache_different_list_value_by_property_name_from_expression(resource_pool, ssm_test_cache,
                                                                             old_property,
                                                                             input_list, cache_property, step_key,
                                                                             input_parameters):
    generate_and_cache_different_list_value_by_property_name(resource_pool, ssm_test_cache, old_property, input_list,
                                                             cache_property, step_key, input_parameters)
