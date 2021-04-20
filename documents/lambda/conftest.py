from pytest_bdd import given, parsers, when, then
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


def __populate_cache_with_memory_size(
        resource_manager, ssm_test_cache, cache_property, step_key, param_key, input_parameters, boto3_session):
    lambda_arn = extract_param_value(input_parameters, param_key, resource_manager, ssm_test_cache)
    memory_size = lambda_utils.get_memory_size(lambda_arn, boto3_session)
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, str(memory_size))


@given(parsers.parse(__cache_memory_size_value_expression))
@when(parsers.parse(__cache_memory_size_value_expression))
def cache_value_alter_ssm(
        resource_manager, ssm_test_cache, cache_property, step_key, input_parameters, boto3_session):
    __populate_cache_with_memory_size(resource_manager,
                                      ssm_test_cache,
                                      cache_property,
                                      step_key,
                                      "LambdaARN",
                                      input_parameters,
                                      boto3_session)


@then(parsers.parse(assert_concurrent_executions_expression))
def assert_concurrent_executions_value(
        resource_manager, ssm_test_cache, boto3_session, input_parameters
):
    lambda_arn = extract_param_value(input_parameters, "LambdaARN", resource_manager, ssm_test_cache)
    expected_concurrent_executions_value = extract_param_value(input_parameters, "InputValue", resource_manager,
                                                               ssm_test_cache)
    actual_concurrent_executions_value = lambda_utils.get_function_concurrency(lambda_arn, boto3_session)
    assert int(actual_concurrent_executions_value) == int(expected_concurrent_executions_value)


@then(parsers.parse(delete_concurrency_expression))
def delete_function_concurrency(
        resource_manager, ssm_test_cache, boto3_session, input_parameters
):
    lambda_arn = extract_param_value(input_parameters, "LambdaARN", resource_manager, ssm_test_cache)
    lambda_utils.delete_function_concurrency(lambda_arn, boto3_session)


@then(parsers.parse(assert_provisioned_concurrency_expression))
def assert_provisioned_concurrency_value(
        resource_manager, ssm_test_cache, boto3_session, input_parameters
):
    lambda_arn = extract_param_value(input_parameters, "LambdaARN", resource_manager, ssm_test_cache)
    qualifier = extract_param_value(input_parameters, "LambdaQualifier", resource_manager, ssm_test_cache)
    expected_provisioned_concurrency_value = extract_param_value(input_parameters, "InputValue", resource_manager,
                                                                 ssm_test_cache)
    actual_provisioned_concurrency_value = lambda_utils.get_function_provisioned_concurrency(
        lambda_arn,
        qualifier,
        boto3_session
    )
    assert int(actual_provisioned_concurrency_value) == int(expected_provisioned_concurrency_value)


@then(parsers.parse(delete_provisioned_concurrency_expression))
def delete_provisioned_concurrency_config(
        resource_manager, ssm_test_cache, boto3_session, input_parameters
):
    lambda_arn = extract_param_value(input_parameters, "LambdaARN", resource_manager, ssm_test_cache)
    qualifier = extract_param_value(input_parameters, "LambdaQualifier", resource_manager, ssm_test_cache)
    lambda_utils.delete_function_provisioned_concurrency_config(lambda_arn, qualifier, boto3_session)
