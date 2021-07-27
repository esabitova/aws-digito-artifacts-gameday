import logging
import re

import jsonpath_ng
import pytest
from pytest_bdd import (
    then,
    when,
    given,
    parsers
)

from resource_manager.src.util.boto3_client_factory import client
from resource_manager.src.util.common_test_utils import generate_and_cache_different_list_value_by_property_name, \
    extract_param_value, put_to_ssm_test_cache
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


@given(parsers.parse('cache by "{method_name}" method of "{service_name}" "{cache_key}"'
                     '\n{input_parameters}'))
@when(parsers.parse('cache by "{method_name}" method of "{service_name}" "{cache_key}"'
                    '\n{input_parameters}'))
@then(parsers.parse('cache by "{method_name}" method of "{service_name}" "{cache_key}"'
                    '\n{input_parameters}'))
def cache_by_method_of_service_name(boto3_session, resource_pool, ssm_document,
                                    cfn_output_params, ssm_test_cache,
                                    method_name, service_name, cache_key, cfn_installed_alarms,
                                    input_parameters):
    service_client = client(service_name, boto3_session)

    parameters = ssm_document.parse_input_parameters(cfn_output_params, cfn_installed_alarms, ssm_test_cache,
                                                     input_parameters)

    arguments = {}
    json_paths = {}
    for parameter, value in parameters.items():
        if isinstance(value, list):
            for v in value:
                if re.match("^\\$.*", v):
                    json_paths[parameter] = v
                else:
                    arguments[parameter] = v
        else:
            if re.match("^\\$.*", value):
                json_paths[parameter] = value
            else:
                arguments[parameter] = value

    response = getattr(service_client, method_name)(**arguments)

    for cache_property, json_path in json_paths.items():
        found = jsonpath_ng.parse(json_path).find(response)
        if found and len(found) > 0:
            if len(found) == 1:
                target_value = found[0].value
            else:
                target_value = [f.value for f in found]
            put_to_ssm_test_cache(ssm_test_cache, cache_key, cache_property, target_value)


@when(parsers.parse('start canary'
                    '\n{input_parameters}'))
def start_canary(boto3_session, cfn_output_params, input_parameters, resource_pool, ssm_test_cache):
    synthetics_client = client("synthetics", boto3_session)
    canary_name = extract_param_value(input_parameters, "CanaryName", resource_pool, ssm_test_cache)
    logger.info(f'Starting canary {canary_name}')
    synthetics_client.start_canary(Name=canary_name)
    logger.info(f'Canary {canary_name} was started')
    ssm_test_cache['CanaryName'] = canary_name


@pytest.fixture(scope='function')
def stop_canary_teardown(boto3_session, resource_pool, ssm_test_cache):
    """
    Use that method as the part of tear down process.
    To call the current method just pass it as an argument into your function
    """
    yield
    synthetics_client = client("synthetics", boto3_session)
    canary_name = ssm_test_cache['CanaryName']
    logger.info(f'Stopping canary {canary_name}')
    synthetics_client.stop_canary(Name=canary_name)
    logger.info(f'Canary {canary_name} was stopped')
