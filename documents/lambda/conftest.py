from pytest_bdd import given, parsers, when
from resource_manager.src.util import lambda_utils
from resource_manager.src.util.common_test_utils import (extract_param_value,
                                                         put_to_ssm_test_cache)

__cache_memory_size_value_expression =\
    'cache value of memory size as "{cache_property}" '\
    'at the lambda "{step_key}" SSM automation execution'\
    '\n{input_parameters}'


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
