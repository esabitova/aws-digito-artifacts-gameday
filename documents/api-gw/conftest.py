from time import sleep

import jsonpath_ng
from pytest_bdd import given, parsers, when, then

from resource_manager.src.util import apigw_util as apigw_util
from resource_manager.src.util.boto3_client_factory import client
from resource_manager.src.util.common_test_utils import extract_param_value, put_to_ssm_test_cache

cache_current_stage_deployment_id_expression = 'cache current deployment id as "{cache_property}" "{step_key}" SSM ' \
                                               'automation execution' \
                                               '\n{input_parameters}'

update_current_stage_deployment_id_expression = 'update current deployment id and cache result as "{cache_property}"' \
                                                ' "{step_key}" SSM automation execution' \
                                                '\n{input_parameters}'

apply_dummy_deployment_to_stage_expression = 'set dummy deployment number "{number}" as current and cache previous ' \
                                             'deployment as "{cache_property}" "{step_key}" SSM automation execution' \
                                             '\n{input_parameters}'

create_dummy_deployment_expression = 'create dummy deployment and cache id as "{cache_property}"' \
                                     ' "{step_key}" SSM automation execution' \
                                     '\n{input_parameters}'

create_dummy_deployment_set_expression = 'create "{count}" dummy deployments with interval "{interval}" seconds and ' \
                                         'cache ids as "{cache_property}" "{step_key}" SSM automation execution' \
                                         '\n{input_parameters}'

delete_dummy_deployment_expression = 'delete dummy deployment' \
                                     '\n{input_parameters}'

delete_dummy_deployment_set_expression = 'delete dummy deployments' \
                                         '\n{input_parameters}'


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


@given(parsers.parse(create_dummy_deployment_expression))
@when(parsers.parse(create_dummy_deployment_expression))
@then(parsers.parse(create_dummy_deployment_expression))
def create_dummy_deployment(
        resource_manager, ssm_test_cache, boto3_session, cache_property, step_key, input_parameters
):
    gateway_id = extract_param_value(
        input_parameters, "RestApiGwId", resource_manager, ssm_test_cache
    )
    created_deployment_id = apigw_util.create_deployment(boto3_session, gateway_id)['id']
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, created_deployment_id)


@given(parsers.parse(create_dummy_deployment_set_expression))
@when(parsers.parse(create_dummy_deployment_set_expression))
@then(parsers.parse(create_dummy_deployment_set_expression))
def create_dummy_deployment_set(
        resource_manager, ssm_test_cache, boto3_session, count, interval, cache_property, step_key, input_parameters
):
    count = int(count)
    interval = int(interval)
    deployment_ids = []
    gateway_id = extract_param_value(input_parameters, "RestApiGwId", resource_manager, ssm_test_cache)
    for counter in range(1, count + 1):
        deployment_ids.append(
            apigw_util.create_deployment(boto3_session, gateway_id, f'Dummy deployment {counter}')['id']
        )
        sleep(interval)

    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, deployment_ids)


@given(parsers.parse(delete_dummy_deployment_expression))
@when(parsers.parse(delete_dummy_deployment_expression))
@then(parsers.parse(delete_dummy_deployment_expression))
def delete_dummy_deployment(
        resource_manager, ssm_test_cache, boto3_session, input_parameters
):
    gateway_id = extract_param_value(
        input_parameters, "RestApiGwId", resource_manager, ssm_test_cache
    )
    deployment_id = extract_param_value(
        input_parameters, "RestDeploymentId", resource_manager, ssm_test_cache
    )
    apigw_util.delete_deployment(boto3_session, gateway_id, deployment_id)
    return True


@given(parsers.parse(delete_dummy_deployment_set_expression))
@when(parsers.parse(delete_dummy_deployment_set_expression))
@then(parsers.parse(delete_dummy_deployment_set_expression))
def delete_dummy_deployment_set(resource_manager, ssm_test_cache, boto3_session, input_parameters):
    gateway_id = extract_param_value(input_parameters, "RestApiGwId", resource_manager, ssm_test_cache)
    dummy_deployments = extract_param_value(input_parameters, "DummyDeployments", resource_manager, ssm_test_cache)
    for deployment_id in dummy_deployments:
        apigw_util.delete_deployment(boto3_session, gateway_id, deployment_id)

    return True


@given(parsers.parse(cache_current_stage_deployment_id_expression))
@when(parsers.parse(cache_current_stage_deployment_id_expression))
@then(parsers.parse(cache_current_stage_deployment_id_expression))
def cache_current_stage_deployment_id(
        resource_manager, ssm_test_cache, boto3_session, cache_property, step_key, input_parameters
):
    gateway_id = extract_param_value(input_parameters, "RestApiGwId", resource_manager, ssm_test_cache)
    stage_name = extract_param_value(input_parameters, "RestStageName", resource_manager, ssm_test_cache)
    current_deployment_id = apigw_util.get_stage(boto3_session, gateway_id, stage_name)['deploymentId']
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, current_deployment_id)


@given(parsers.parse(update_current_stage_deployment_id_expression))
@when(parsers.parse(update_current_stage_deployment_id_expression))
@then(parsers.parse(update_current_stage_deployment_id_expression))
def update_current_stage_deployment_id(
        resource_manager, ssm_test_cache, boto3_session, cache_property, step_key, input_parameters
):
    gateway_id = extract_param_value(input_parameters, "RestApiGwId", resource_manager, ssm_test_cache)
    stage_name = extract_param_value(input_parameters, "RestStageName", resource_manager, ssm_test_cache)
    deployment_id = extract_param_value(input_parameters, "RestDeploymentId", resource_manager, ssm_test_cache)
    updated_deployment_id = apigw_util.update_stage_deployment(
        boto3_session, gateway_id, stage_name, deployment_id
    )['deploymentId']
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, updated_deployment_id)


@given(parsers.parse(apply_dummy_deployment_to_stage_expression))
@when(parsers.parse(apply_dummy_deployment_to_stage_expression))
@then(parsers.parse(apply_dummy_deployment_to_stage_expression))
def apply_dummy_deployment_to_stage(
        resource_manager, ssm_test_cache, boto3_session, number, cache_property, step_key, input_parameters
):
    number = int(number) - 1
    gateway_id = extract_param_value(input_parameters, "RestApiGwId", resource_manager, ssm_test_cache)
    stage_name = extract_param_value(input_parameters, "RestStageName", resource_manager, ssm_test_cache)
    dummy_deployments = extract_param_value(input_parameters, "DummyDeployments", resource_manager, ssm_test_cache)
    dummy_deployment_id = dummy_deployments[number]
    previous_deployment_id = dummy_deployments[number - 1]
    apigw_util.update_stage_deployment(boto3_session, gateway_id, stage_name, dummy_deployment_id)
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, previous_deployment_id)
