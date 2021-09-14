import json
import logging

import pytest
from pytest_bdd import (
    then,
    when,
    given,
    parsers
)
from sttable import parse_str_table

from resource_manager.src.util import param_utils
from resource_manager.src.util.boto3_client_factory import client
from resource_manager.src.util.common_test_utils import check_security_group_exists, do_cache_by_method_of_service
from resource_manager.src.util.common_test_utils import generate_and_cache_different_list_value_by_property_name, \
    extract_param_value, put_to_ssm_test_cache
from resource_manager.src.util.common_test_utils import generate_and_cache_different_value_by_property_name
from resource_manager.src.util.common_test_utils import generate_random_string_with_prefix
from resource_manager.src.util.enums.lambda_invocation_type import LambdaInvocationType
from resource_manager.src.util.lambda_utils import trigger_lambda
from resource_manager.src.util.param_utils import parse_param_value

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


@then(parsers.parse('assert "{expected_property}" at "{step_key_for_expected}" '
                    'in "{actual_property}" at "{step_key_for_actual}"'))
def assert_value_isin(ssm_test_cache, expected_property, step_key_for_expected, actual_property, step_key_for_actual):
    temp_var = ssm_test_cache[step_key_for_actual][actual_property]
    if isinstance(temp_var, (list, tuple, dict)):
        assert ssm_test_cache[step_key_for_expected][expected_property] in \
               ssm_test_cache[step_key_for_actual][actual_property]
    else:
        raise AssertionError(f'{actual_property} needs to be one of list, tuple, dict')


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


@given(parsers.parse('cache the size of "{reference}" list as "{cache_property}" "{cache_key}"'))
@when(parsers.parse('cache the size of "{reference}" list as "{cache_property}" "{cache_key}"'))
@then(parsers.parse('cache the size of "{reference}" list as "{cache_property}" "{cache_key}"'))
def cache_the_size_of_list(resource_pool, ssm_document, cfn_installed_alarms,
                           cfn_output_params, ssm_test_cache,
                           reference, cache_property, cache_key):
    reference_value = param_utils.parse_param_value(reference, {'cache': ssm_test_cache,
                                                                'cfn-output': cfn_output_params,
                                                                'alarm': cfn_installed_alarms})
    if isinstance(reference_value, (list, dict, tuple)):  # if it is a sequence or dict
        put_to_ssm_test_cache(ssm_test_cache, cache_key, cache_property, len(reference_value))
    else:  # if it is a scalar
        put_to_ssm_test_cache(ssm_test_cache, cache_key, cache_property, 1)


@given(parsers.parse('cache by "{method_name}" method of "{service_name}" to "{cache_key}"'
                     '\n{input_parameters}'))
@when(parsers.parse('cache by "{method_name}" method of "{service_name}" to "{cache_key}"'
                    '\n{input_parameters}'))
@then(parsers.parse('cache by "{method_name}" method of "{service_name}" to "{cache_key}"'
                    '\n{input_parameters}'))
def cache_by_method_of_service(boto3_session, resource_pool, ssm_document,
                               cfn_output_params, ssm_test_cache,
                               method_name, service_name, cache_key, input_parameters, cfn_installed_alarms):
    """
    Dynamically cache properties from the boto3 method response by specifying boto3 method_name, arguments for boto3
    method_name, JSONPaths to extract properties from a response in input_parameters.
    For boto3 method arguments, the parameter name should start with "Input-" prefix and as the value have either the
    reference to the ssm_test_cache container, or to the cfn_output_container, or to the alarm container,
    or to be just the simple string.
    For output properties the, parameter name should start with "Output-" prefix and the value should be the valid
    JSONPath which will be applied to the response of the boto3 method_name of specified service_name
    :param method_name: boto3 method name
    :param service_name: AWS service name
    :param input_parameters: List of JSONPaths for outputs and other values for inputs (references and simple values)
    :return: Dict with extracted properties by specified JSONPaths
    """
    service_client = client(service_name, boto3_session)

    parameters = ssm_document.parse_input_parameters(cfn_output_params, cfn_installed_alarms, ssm_test_cache,
                                                     input_parameters)

    do_cache_by_method_of_service(cache_key, method_name, parameters, service_client, ssm_test_cache)


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


@given(parsers.parse('invoke lambda "{lambda_arn}" with parameters\n{input_parameters_table}'))
@when(parsers.parse('invoke lambda "{lambda_arn}" with parameters\n{input_parameters_table}'))
@then(parsers.parse('invoke lambda "{lambda_arn}" with parameters\n{input_parameters_table}'))
def invoke_lambda_function_async_with_parameters(
        boto3_session, resource_pool, cfn_output_params, ssm_test_cache, lambda_arn, input_parameters_table
):
    parameters = parse_str_table(input_parameters_table, False).rows

    lambda_arn = parse_param_value(lambda_arn, {'cache': ssm_test_cache, 'cfn-output': cfn_output_params})
    lambda_params = {}
    for item in parameters:
        param_name = item['0']
        param_value = parse_param_value(item['1'], {'cache': ssm_test_cache, 'cfn-output': cfn_output_params})
        lambda_params[param_name] = param_value

    payload = json.dumps(lambda_params)

    logging.info(f'Invoke lambda {lambda_arn} ...')
    result = trigger_lambda(lambda_arn=lambda_arn,
                            payload=payload,
                            invocation_type=LambdaInvocationType.Event,
                            session=boto3_session)
    logging.info(f'Lambda StatusCode: {result["StatusCode"]}')
    logging.info(f'Lambda Request ID: {result["ResponseMetadata"]["RequestId"]}')
