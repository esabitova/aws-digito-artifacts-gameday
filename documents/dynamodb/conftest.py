import jsonpath_ng
from pytest_bdd import (
    given,
    when
)
from pytest_bdd.parsers import parse

from resource_manager.src.util.common_test_utils import extract_param_value, generate_different_value_by_ranges
from resource_manager.src.util.common_test_utils import put_to_ssm_test_cache


@given(parse('cache value of "{json_path}" as "{cache_property}" "{step_key}" SSM automation execution'
             '\n{input_parameters}'))
@when(parse('cache value of "{json_path}" as "{cache_property}" "{step_key}" SSM automation execution'
            '\n{input_parameters}'))
def cache_value(resource_manager, ssm_test_cache, boto3_session, json_path, cache_property, step_key,
                input_parameters):
    dynamodb_client = boto3_session.client('dynamodb')
    table_name_value = extract_param_value(input_parameters, 'TableName', resource_manager, ssm_test_cache)
    response = dynamodb_client.describe_table(TableName=table_name_value)
    target_value = jsonpath_ng.parse(json_path).find(response)[0].value
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, target_value)


@given(parse('generate different value of "{target_property}" than "{old_property}" from "{from_range}" to'
             ' "{to_range}" as "{new_property}" "{step_key}" SSM automation execution'
             '\n{input_parameters}'))
@when(parse('generate different value of "{target_property}" than "{old_property}" from "{from_range}" to'
            ' "{to_range}" as "{new_property}" "{step_key}" SSM automation execution'
            '\n{input_parameters}'))
def generate_different_value(resource_manager, ssm_test_cache, target_property, old_property, from_range, to_range,
                             new_property, step_key, input_parameters):
    old_value = extract_param_value(input_parameters, old_property, resource_manager, ssm_test_cache)
    new_value = generate_different_value_by_ranges(int(from_range), int(to_range), int(old_value))
    put_to_ssm_test_cache(ssm_test_cache, step_key, new_property, new_value)
