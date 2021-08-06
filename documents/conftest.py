import logging
import pytest
from pytest_bdd import (
    then,
    when,
    given,
    parsers
)

from resource_manager.src.util.boto3_client_factory import client
from resource_manager.src.util.common_test_utils import generate_and_cache_different_list_value_by_property_name, \
    extract_param_value
from resource_manager.src.util.common_test_utils import generate_and_cache_different_value_by_property_name
from resource_manager.src.util.common_test_utils import generate_random_string_with_prefix
from resource_manager.src.util.common_test_utils import check_security_group_exists

logger = logging.getLogger(__name__)


@given(parsers.parse('generate and cache random string with prefix {prefix} as {field_name}'))
def generate_and_cache_random_string_with_prefix(ssm_test_cache, prefix, field_name):
    rnd = generate_random_string_with_prefix(prefix)
    ssm_test_cache[field_name] = rnd


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


@then(parsers.parse('assert security group "{expected_property}" at "{step_key_for_expected}" was removed'))
def assert_security_group_removed(ssm_test_cache, boto3_session, expected_property, step_key_for_expected):
    security_group_id = ssm_test_cache[step_key_for_expected][expected_property]
    assert check_security_group_exists(boto3_session, security_group_id) is False


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


@when(parsers.parse('start canary\n{input_parameters}'))
def start_canary(boto3_session, input_parameters, resource_pool, ssm_test_cache, canary_for_teardown):
    """
    Start canary name with name passed as CanaryName
    """
    synthetics_client = client("synthetics", boto3_session)
    canary_name = extract_param_value(input_parameters, "CanaryName", resource_pool, ssm_test_cache)
    canary_for_teardown['CanaryName'] = canary_name
    logger.info(f'Starting canary {canary_name}')
    synthetics_client.start_canary(Name=canary_name)
    logger.info(f'Canary {canary_name} was started')


@pytest.fixture(scope='function')
def canary_for_teardown(boto3_session, ssm_test_cache):
    """
    Fixture to stop canary at test teardown
    """
    canary = {}
    yield canary
    canary_name = canary.get('CanaryName')
    if canary_name:
        synthetics_client = client("synthetics", boto3_session)
        logger.info(f'Stopping canary {canary_name}')
        synthetics_client.stop_canary(Name=canary_name)
        logger.info(f'Canary {canary_name} was stopped')
