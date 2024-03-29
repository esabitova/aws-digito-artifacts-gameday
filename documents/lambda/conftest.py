import time
from pytest_bdd import given, parsers, when, then

import resource_manager.src.constants as constants
from resource_manager.src.util import lambda_utils
from resource_manager.src.util.common_test_utils import (extract_param_value,
                                                         put_to_ssm_test_cache)

__cache_memory_size_value_expression = \
    'cache value of memory size as "{cache_property}" ' \
    'at the lambda "{step_key}" SSM automation execution' \
    '\n{input_parameters}'
assert_concurrent_executions_expression = 'assert current concurrent executions value is equal to input value' \
                                          '\n{input_parameters}'
delete_concurrency_expression = 'delete function concurrency\n{input_parameters}'
assert_provisioned_concurrency_expression = 'assert current provisioned concurrency is equal to input value' \
                                            '\n{input_parameters}'
delete_provisioned_concurrency_expression = 'delete provisioned concurrency config\n{input_parameters}'
lambda_state_expression = 'wait for lambda to be in active state for "{time_to_wait}" seconds' \
                          '\n{input_parameters}'
create_alias_expression = 'create alias and cache its name as "{cache_property}" at step "{step_key}"' \
                          '\n{input_parameters}'
delete_alias_expression = 'delete alias\n{input_parameters}'
wait_memory_changed_expression = 'wait for lambda memory size to have a new value for "{time_to_wait:d}" seconds' \
                                 '\n{input_parameters}'
publish_function_version_expression = 'published function version and cached version as "{cache_property}"' \
                                      ' at step "{step_key}"' \
                                      '\n{input_parameters}'
assert_alias_version_expression = 'assert version in alias changed\n{input_parameters}'
delete_function_version_expression = 'delete function version\n{input_parameters}'
invoke_throttled_function_expression = 'invoke throttled function\n{input_parameters}'
invoke_ordinary_function_expression = 'invoke ordinary function\n{input_parameters}'
cache_current_time_limit_expression = 'cached current execution time limit as "{cache_property}" at step "{step_key}"' \
                                      '\n{input_parameters}'
assert_execution_time_limit_expression = 'assert execution time limit is equal to input value\n{input_parameters}'


def __populate_cache_with_memory_size(
        resource_pool, ssm_test_cache, cache_property, step_key, param_key, input_parameters, boto3_session):
    lambda_arn = extract_param_value(input_parameters, param_key, resource_pool, ssm_test_cache)
    memory_size = lambda_utils.get_memory_size(lambda_arn, boto3_session)
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, str(memory_size))


@given(parsers.parse(create_alias_expression))
def create_alias(
        resource_pool, ssm_test_cache, cache_property, step_key, input_parameters, boto3_session
):
    lambda_arn = extract_param_value(input_parameters, "LambdaARN", resource_pool, ssm_test_cache)
    lambda_version = extract_param_value(input_parameters, "LambdaVersion", resource_pool, ssm_test_cache)
    alias_name = "alias_" + time.strftime("%Y_%d_%m_%H_%M_%S", time.gmtime())
    lambda_utils.create_alias(lambda_arn, alias_name, lambda_version, boto3_session)
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, alias_name)


@when(parsers.parse(lambda_state_expression))
@then(parsers.parse(lambda_state_expression))
def wait_for_lambda_state(
        resource_pool, ssm_test_cache, input_parameters, time_to_wait, boto3_session
):
    lambda_arn = extract_param_value(input_parameters, "LambdaARN", resource_pool, ssm_test_cache)
    lambda_state = lambda_utils.get_lambda_state(lambda_arn, boto3_session)
    start_time = time.time()
    elapsed_time = time.time() - start_time
    while lambda_state != 'Active':
        if elapsed_time > int(time_to_wait):
            raise Exception(f'Waiting for lambda {lambda_arn} to be active timed out')
        time.sleep(constants.sleep_time_secs)
        elapsed_time = time.time() - start_time
        lambda_state = lambda_utils.get_lambda_state(lambda_arn, boto3_session)
    return True


@then(parsers.parse(delete_alias_expression))
def delete_alias(
        resource_pool, ssm_test_cache, input_parameters, boto3_session
):
    lambda_arn = extract_param_value(input_parameters, "LambdaARN", resource_pool, ssm_test_cache)
    alias_name = extract_param_value(input_parameters, "AliasName", resource_pool, ssm_test_cache)
    lambda_utils.delete_alias(lambda_arn, alias_name, boto3_session)


@given(parsers.parse(wait_memory_changed_expression))
@when(parsers.parse(wait_memory_changed_expression))
@then(parsers.parse(wait_memory_changed_expression))
def wait_memory_changed(resource_pool, ssm_test_cache, time_to_wait, input_parameters, boto3_session):
    lambda_arn = extract_param_value(input_parameters, "LambdaARN", resource_pool, ssm_test_cache)
    expected_memory_size = int(extract_param_value(input_parameters, "MemorySize", resource_pool, ssm_test_cache))

    lambda_utils.do_wait_for_memory_changed(lambda_arn, expected_memory_size, time_to_wait, boto3_session)


@given(parsers.parse(__cache_memory_size_value_expression))
@when(parsers.parse(__cache_memory_size_value_expression))
@then(parsers.parse(__cache_memory_size_value_expression))
def cache_value_alter_ssm(
        resource_pool, ssm_test_cache, cache_property, step_key, input_parameters, boto3_session):
    __populate_cache_with_memory_size(resource_pool,
                                      ssm_test_cache,
                                      cache_property,
                                      step_key,
                                      "LambdaARN",
                                      input_parameters,
                                      boto3_session)


@then(parsers.parse(assert_concurrent_executions_expression))
def assert_concurrent_executions_value(
        resource_pool, ssm_test_cache, boto3_session, input_parameters
):
    lambda_arn = extract_param_value(input_parameters, "LambdaARN", resource_pool, ssm_test_cache)
    expected_concurrent_executions_value = extract_param_value(input_parameters, "InputValue", resource_pool,
                                                               ssm_test_cache)
    actual_concurrent_executions_value = lambda_utils.get_function_concurrency(lambda_arn, boto3_session)
    assert int(actual_concurrent_executions_value) == int(expected_concurrent_executions_value)


@then(parsers.parse(delete_concurrency_expression))
def delete_function_concurrency(
        resource_pool, ssm_test_cache, boto3_session, input_parameters
):
    lambda_arn = extract_param_value(input_parameters, "LambdaARN", resource_pool, ssm_test_cache)
    lambda_utils.delete_function_concurrency(lambda_arn, boto3_session)


@then(parsers.parse(assert_provisioned_concurrency_expression))
def assert_provisioned_concurrency_value(
        resource_pool, ssm_test_cache, boto3_session, input_parameters
):
    lambda_arn = extract_param_value(input_parameters, "LambdaARN", resource_pool, ssm_test_cache)
    qualifier = extract_param_value(input_parameters, "LambdaQualifier", resource_pool, ssm_test_cache)
    expected_provisioned_concurrency_value = extract_param_value(input_parameters, "InputValue", resource_pool,
                                                                 ssm_test_cache)
    actual_provisioned_concurrency_value = lambda_utils.get_function_provisioned_concurrency(
        lambda_arn,
        qualifier,
        boto3_session
    )
    assert int(actual_provisioned_concurrency_value) == int(expected_provisioned_concurrency_value)


@then(parsers.parse(delete_provisioned_concurrency_expression))
def delete_provisioned_concurrency_config(
        resource_pool, ssm_test_cache, boto3_session, input_parameters
):
    lambda_arn = extract_param_value(input_parameters, "LambdaARN", resource_pool, ssm_test_cache)
    qualifier = extract_param_value(input_parameters, "LambdaQualifier", resource_pool, ssm_test_cache)
    lambda_utils.delete_function_provisioned_concurrency_config(lambda_arn, qualifier, boto3_session)


@when(parsers.parse(publish_function_version_expression))
@given(parsers.parse(publish_function_version_expression))
def publish_function_version(
        resource_pool, ssm_test_cache, cache_property, step_key, input_parameters, boto3_session
):
    lambda_arn = extract_param_value(input_parameters, "LambdaARN", resource_pool, ssm_test_cache)
    response = lambda_utils.publish_version(lambda_arn, boto3_session)
    version = response.get('Version')
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, version)


@then(parsers.parse(assert_alias_version_expression))
def assert_version_in_alias(
        resource_pool, ssm_test_cache, input_parameters, boto3_session
):
    lambda_arn = extract_param_value(input_parameters, "LambdaARN", resource_pool, ssm_test_cache)
    alias_name = extract_param_value(input_parameters, "AliasName", resource_pool, ssm_test_cache)
    expected_version = extract_param_value(input_parameters, "LambdaVersion", resource_pool, ssm_test_cache)
    actual_version = lambda_utils.get_alias_version(lambda_arn, alias_name, boto3_session)
    assert str(expected_version) == str(actual_version)


@when(parsers.parse(delete_function_version_expression))
@then(parsers.parse(delete_function_version_expression))
def delete_version(
        resource_pool, ssm_test_cache, input_parameters, boto3_session
):
    lambda_arn = extract_param_value(input_parameters, "LambdaARN", resource_pool, ssm_test_cache)
    lambda_version = extract_param_value(input_parameters, "LambdaVersion", resource_pool, ssm_test_cache)
    lambda_utils.delete_function_version(lambda_arn, lambda_version, boto3_session)


@when(parsers.parse(invoke_throttled_function_expression))
def invoke_throttled_function(
        resource_pool, ssm_test_cache, input_parameters, boto3_session
):
    lambda_arn = extract_param_value(input_parameters, "LambdaARN", resource_pool, ssm_test_cache)
    lambda_utils.trigger_throttled_lambda(lambda_arn, boto3_session)


@when(parsers.parse(invoke_ordinary_function_expression))
def invoke_ordinary_function(
        resource_pool, ssm_test_cache, input_parameters, boto3_session
):
    lambda_arn = extract_param_value(input_parameters, "LambdaARN", resource_pool, ssm_test_cache)
    lambda_utils.trigger_ordinary_lambda(lambda_arn, boto3_session)


@when(parsers.parse('invoke ordinary function "{invoke_attempts:d}" '
                    'times\n{input_parameters}'))
def invoke_ordinary_function_several_times(
        resource_pool, ssm_test_cache, input_parameters, boto3_session, invoke_attempts
):
    lambda_arn = extract_param_value(input_parameters, "LambdaARN", resource_pool, ssm_test_cache)
    lambda_utils.trigger_ordinary_lambda_several_times(lambda_arn, boto3_session, invoke_attempts)


@when(parsers.parse('test lambda function under stress "{overall_stress_time:d}" seconds overall '
                    'with "{number_in_each_chunk:d}" invokes in each test '
                    'and "{delay_among_chunks:d}" seconds delay\n{input_parameters}'))
def invoke_function_under_stress(
        resource_pool, ssm_test_cache, input_parameters, boto3_session, overall_stress_time,
        number_in_each_chunk, delay_among_chunks
):
    lambda_arn = extract_param_value(input_parameters, "LambdaARN", resource_pool, ssm_test_cache)
    lambda_utils.trigger_lambda_under_stress(lambda_arn, boto3_session, overall_stress_time,
                                             number_in_each_chunk, delay_among_chunks)


@given(parsers.parse(cache_current_time_limit_expression))
@then(parsers.parse(cache_current_time_limit_expression))
@when(parsers.parse(cache_current_time_limit_expression))
def cache_current_time_limit(
        resource_pool, ssm_test_cache, cache_property, step_key, input_parameters, boto3_session
):
    lambda_arn = extract_param_value(input_parameters, "LambdaARN", resource_pool, ssm_test_cache)
    time_limit_value = lambda_utils.get_function_execution_time_limit(lambda_arn, boto3_session)
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, time_limit_value)


@given(parsers.parse(assert_execution_time_limit_expression))
@then(parsers.parse(assert_execution_time_limit_expression))
@when(parsers.parse(assert_execution_time_limit_expression))
def assert_execution_time_limit(
        resource_pool, ssm_test_cache, input_parameters, boto3_session
):
    lambda_arn = extract_param_value(input_parameters, "LambdaARN", resource_pool, ssm_test_cache)
    expected_time_limit = extract_param_value(input_parameters, "ExpectedValue", resource_pool, ssm_test_cache)
    actual_time_limit = lambda_utils.get_function_execution_time_limit(lambda_arn, boto3_session)
    assert int(expected_time_limit) == int(actual_time_limit)
