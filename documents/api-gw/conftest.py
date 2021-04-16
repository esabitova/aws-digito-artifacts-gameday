from pytest_bdd import given, parsers, when
from resource_manager.src.util.common_test_utils import (extract_param_value,
                                                         put_to_ssm_test_cache)
from resource_manager.src.util.boto3_client_factory import client
import jsonpath_ng


@given(parsers.parse('cache API GW property "{json_path}" as "{cache_property}" "{step_key}" SSM automation execution'
                     '\n{input_parameters}'))
@when(parsers.parse('cache API GW property "{json_path}" as "{cache_property}" "{step_key}" SSM automation execution'
                    '\n{input_parameters}'))
def cache_apigw_property(resource_manager, ssm_test_cache, boto3_session, json_path, cache_property, step_key,
                         input_parameters):
    apigw_usage_plan_id = extract_param_value(input_parameters, 'RestApiGwUsagePlanId', resource_manager,
                                              ssm_test_cache)
    apigw_client = client('apigateway', boto3_session)
    response = apigw_client.get_usage_plan(usagePlanId=apigw_usage_plan_id)
    target_value = jsonpath_ng.parse(json_path).find(response)[0].value
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, target_value)
