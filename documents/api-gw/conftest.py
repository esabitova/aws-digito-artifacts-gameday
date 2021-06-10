import json
import logging
from time import sleep

import jsonpath_ng
import pytest
import requests
from websocket import create_connection
from websocket._exceptions import WebSocketBadStatusException
from pytest_bdd import (
    given, parsers, when, then
)

from resource_manager.src.util import apigw2_utils as apigw2_utils
from resource_manager.src.util import apigw_utils as apigw_utils
from resource_manager.src.util.boto3_client_factory import client
from resource_manager.src.util.common_test_utils import (
    extract_param_value, put_to_ssm_test_cache, extract_and_cache_param_values
)
from resource_manager.src.util.enums.lambda_invocation_type import LambdaInvocationType
from resource_manager.src.util.lambda_utils import trigger_lambda

cache_current_stage_deployment_id_expression = 'cache current deployment id as "{cache_property}" "{step_key}" SSM ' \
                                               'automation execution' \
                                               '\n{input_parameters}'

cache_current_wshttp_stage_deployment_id_expression = 'cache current ws or http deployment id as "{cache_property}"' \
                                                      ' "{step_key}" SSM automation execution' \
                                                      '\n{input_parameters}'

update_current_stage_deployment_id_expression = 'update current deployment id and cache result as "{cache_property}"' \
                                                ' "{step_key}" SSM automation execution' \
                                                '\n{input_parameters}'

apply_dummy_deployment_to_stage_expression = 'set dummy deployment number "{number}" as current and cache previous ' \
                                             'deployment as "{cache_property}" "{step_key}" SSM automation execution' \
                                             '\n{input_parameters}'

apply_dummy_wshttp_deployment_to_stage_expression = 'set dummy ws or http deployment number "{number}" as current ' \
                                                    'and cache previous deployment as "{cache_property}" "{step_key}"' \
                                                    ' SSM automation execution' \
                                                    '\n{input_parameters}'

create_dummy_deployment_expression = 'create dummy deployment and cache id as "{cache_property}"' \
                                     ' "{step_key}" SSM automation execution' \
                                     '\n{input_parameters}'

create_dummy_wshttp_deployment_expression = 'create dummy ws or http deployment and cache id as "{cache_property}"' \
                                            ' "{step_key}" SSM automation execution' \
                                            '\n{input_parameters}'

create_dummy_deployment_set_expression = 'create "{count}" dummy deployments with interval "{interval}" seconds and ' \
                                         'cache ids as "{cache_property}" "{step_key}" SSM automation execution' \
                                         '\n{input_parameters}'

create_dummy_wshttp_deployments_set_expression = 'create "{count}" dummy ws or http deployments with interval ' \
                                                 '"{interval}" seconds and cache ids as "{cache_property}" ' \
                                                 '"{step_key}" SSM automation execution' \
                                                 '\n{input_parameters}'

delete_dummy_deployment_expression = 'delete dummy deployment' \
                                     '\n{input_parameters}'

delete_dummy_deployment_set_expression = 'delete dummy deployments' \
                                         '\n{input_parameters}'

cache_param_values_for_teardown_expression = 'cache value of "{param_list}" "{step_key}" SSM automation execution for' \
                                             ' teardown' \
                                             '\n{input_parameters}'

cache_param_values_expression = 'cache value of "{param_list}" "{step_key}" SSM automation execution' \
                                '\n{input_parameters}'

cache_throttling_settings_expression = 'cache usage plan rate limit as "{rate_limit_key}" and ' \
                                       'burst limit as "{burst_limit_key}" "{step_key}" SSM automation execution'

get_api_key_and_perform_http_requests_expression = 'get value of API key "{key_id}" and perform "{count}" http ' \
                                                   'requests with delay "{delay}" seconds using stage URL "{url}"' \
                                                   '\n{input_parameters}'

get_api_key_and_invoke_lambda_to_perform_http_requests = 'get API key "{api_key_id_ref}" and invoke lambda ' \
                                                         '"{lambda_arn_ref}" to perform "{count}" http requests ' \
                                                         'with interval "{interval}" seconds'

cache_vpc_endpoint_security_groups_map = 'get REST API Gateway endpoints and their security groups, ' \
                                         'cache map as "{cache_property}" "{step_key}" SSM automation execution'

cache_httpws_default_throttling_settings = 'cache default route throttling rate limit as "{rate_limit_key}" and ' \
                                           'burst limit as "{burst_limit_key}" "{step_key}" SSM automation execution' \
                                           '\n{input_parameters}'

cache_httpws_route_throttling_settings = 'cache route throttling rate limit as "{rate_limit_key}" and ' \
                                         'burst limit as "{burst_limit_key}" "{step_key}" SSM automation execution' \
                                         '\n{input_parameters}'


@given(parsers.parse('cache API GW property "{json_path}" as "{cache_property}" "{step_key}" SSM automation execution'
                     '\n{input_parameters}'))
@when(parsers.parse('cache API GW property "{json_path}" as "{cache_property}" "{step_key}" SSM automation execution'
                    '\n{input_parameters}'))
@then(parsers.parse('cache API GW property "{json_path}" as "{cache_property}" "{step_key}" SSM automation execution'
                    '\n{input_parameters}'))
def cache_apigw_property(resource_pool, ssm_test_cache, boto3_session, json_path, cache_property, step_key,
                         input_parameters):
    apigw_usage_plan_id = extract_param_value(input_parameters, 'RestApiGwUsagePlanId', resource_pool,
                                              ssm_test_cache)
    apigw_client = client('apigateway', boto3_session)
    response = apigw_client.get_usage_plan(usagePlanId=apigw_usage_plan_id)
    target_value = jsonpath_ng.parse(json_path).find(response)[0].value
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, target_value)


@given(parsers.parse(create_dummy_deployment_expression))
@when(parsers.parse(create_dummy_deployment_expression))
@then(parsers.parse(create_dummy_deployment_expression))
def create_dummy_deployment(
        resource_pool, ssm_test_cache, boto3_session, cache_property, step_key, input_parameters
):
    gateway_id = extract_param_value(
        input_parameters, "RestApiGwId", resource_pool, ssm_test_cache
    )
    created_deployment_id = apigw_utils.create_deployment(boto3_session, gateway_id)['id']
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, created_deployment_id)


@pytest.fixture(scope='function')
def dummy_wshttp_deployment(boto3_session):
    dummy_deployment = {}
    yield dummy_deployment
    gateway_id = dummy_deployment['HttpWsApiGwId']
    dummy_deployment_id = dummy_deployment['HttpWsDeploymentId']
    backup_deployment_id = dummy_deployment['BackupDeploymentId']
    stage_name = dummy_deployment['HttpWsStageName']
    stage = apigw2_utils.get_stage(boto3_session, gateway_id, stage_name)
    # Teardown for tests with dummy deployment
    # Rollback to original deployment id and delete dummy deployment
    # Ignore rollback for autodeploy stages
    if 'AutoDeploy' not in stage or stage['AutoDeploy'] is False:
        logging.info(f'Rollback stage {stage_name} to deployment {backup_deployment_id}')
        updated_deployment_id = apigw2_utils.update_stage_deployment(
            boto3_session, gateway_id, stage_name, backup_deployment_id
        )['DeploymentId']
        assert updated_deployment_id == backup_deployment_id
    logging.info(f'Delete dummy deployment {dummy_deployment_id}')
    apigw2_utils.delete_deployment(boto3_session, gateway_id, dummy_deployment_id)


@given(parsers.parse(create_dummy_wshttp_deployment_expression))
@when(parsers.parse(create_dummy_wshttp_deployment_expression))
@then(parsers.parse(create_dummy_wshttp_deployment_expression))
def create_dummy_wshttp_deployment(
        resource_pool, ssm_test_cache, boto3_session, dummy_wshttp_deployment, cache_property, step_key,
        input_parameters
):
    gateway_id = extract_param_value(input_parameters, "HttpWsApiGwId", resource_pool, ssm_test_cache)
    backup_deployment_id = extract_param_value(input_parameters, "BackupDeploymentId", resource_pool, ssm_test_cache)
    stage_name = extract_param_value(input_parameters, "HttpWsStageName", resource_pool, ssm_test_cache)
    created_deployment_id = apigw2_utils.create_deployment(boto3_session, gateway_id)['DeploymentId']
    # Prepare teardown
    dummy_wshttp_deployment['HttpWsApiGwId'] = gateway_id
    dummy_wshttp_deployment['HttpWsDeploymentId'] = created_deployment_id
    dummy_wshttp_deployment['BackupDeploymentId'] = backup_deployment_id
    dummy_wshttp_deployment['HttpWsStageName'] = stage_name
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, created_deployment_id)


@given(parsers.parse(create_dummy_deployment_set_expression))
@when(parsers.parse(create_dummy_deployment_set_expression))
@then(parsers.parse(create_dummy_deployment_set_expression))
def create_dummy_deployment_set(
        resource_pool, ssm_test_cache, boto3_session, count, interval, cache_property, step_key, input_parameters
):
    count = int(count)
    interval = int(interval)
    deployment_ids = []
    gateway_id = extract_param_value(input_parameters, "RestApiGwId", resource_pool, ssm_test_cache)
    for counter in range(1, count + 1):
        deployment_ids.append(
            apigw_utils.create_deployment(boto3_session, gateway_id, f'Dummy deployment {counter}')['id']
        )
        sleep(interval)

    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, deployment_ids)


@pytest.fixture(scope='function')
def dummy_wshttp_deployments_set(boto3_session):
    dummy_deployments_set = {}
    yield dummy_deployments_set
    gateway_id = dummy_deployments_set['HttpWsApiGwId']
    dummy_deployments_ids = dummy_deployments_set['HttpWsDeploymentIds']
    backup_deployment_id = dummy_deployments_set['BackupDeploymentId']
    stage_name = dummy_deployments_set['HttpWsStageName']
    stage = apigw2_utils.get_stage(boto3_session, gateway_id, stage_name)
    # Teardown for tests with dummy deployment
    # Rollback to original deployment id and delete dummy deployment
    # Ignore rollback for autodeploy stages
    if 'AutoDeploy' not in stage or stage['AutoDeploy'] is False:
        logging.info(f'Rollback stage {stage_name} to deployment {backup_deployment_id}')
        updated_deployment_id = apigw2_utils.update_stage_deployment(
            boto3_session, gateway_id, stage_name, backup_deployment_id
        )['DeploymentId']
        assert updated_deployment_id == backup_deployment_id
    logging.info('Delete dummy deployments')
    for dummy_deployment_id in dummy_deployments_ids:
        apigw2_utils.delete_deployment(boto3_session, gateway_id, dummy_deployment_id)


@given(parsers.parse(create_dummy_wshttp_deployments_set_expression))
@when(parsers.parse(create_dummy_wshttp_deployments_set_expression))
@then(parsers.parse(create_dummy_wshttp_deployments_set_expression))
def create_dummy_wshttp_deployments_set(
        resource_pool, ssm_test_cache, boto3_session, dummy_wshttp_deployments_set, count, interval, cache_property,
        step_key, input_parameters
):
    gateway_id = extract_param_value(input_parameters, "HttpWsApiGwId", resource_pool, ssm_test_cache)
    backup_deployment_id = extract_param_value(input_parameters, "BackupDeploymentId", resource_pool, ssm_test_cache)
    stage_name = extract_param_value(input_parameters, "HttpWsStageName", resource_pool, ssm_test_cache)
    count = int(count)
    interval = int(interval)
    deployment_ids = []
    for counter in range(1, count + 1):
        deployment_ids.append(
            apigw2_utils.create_deployment(boto3_session, gateway_id, f'Dummy deployment {counter}')['DeploymentId']
        )
        sleep(interval)

    # Prepare teardown
    dummy_wshttp_deployments_set['HttpWsApiGwId'] = gateway_id
    dummy_wshttp_deployments_set['HttpWsDeploymentIds'] = deployment_ids
    dummy_wshttp_deployments_set['BackupDeploymentId'] = backup_deployment_id
    dummy_wshttp_deployments_set['HttpWsStageName'] = stage_name
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, deployment_ids)


@given(parsers.parse(delete_dummy_deployment_expression))
@when(parsers.parse(delete_dummy_deployment_expression))
@then(parsers.parse(delete_dummy_deployment_expression))
def delete_dummy_deployment(
        resource_pool, ssm_test_cache, boto3_session, input_parameters
):
    gateway_id = extract_param_value(input_parameters, "RestApiGwId", resource_pool, ssm_test_cache)
    deployment_id = extract_param_value(input_parameters, "RestDeploymentId", resource_pool, ssm_test_cache)
    apigw_utils.delete_deployment(boto3_session, gateway_id, deployment_id)
    return True


@given(parsers.parse(delete_dummy_deployment_set_expression))
@when(parsers.parse(delete_dummy_deployment_set_expression))
@then(parsers.parse(delete_dummy_deployment_set_expression))
def delete_dummy_deployment_set(resource_pool, ssm_test_cache, boto3_session, input_parameters):
    gateway_id = extract_param_value(input_parameters, "RestApiGwId", resource_pool, ssm_test_cache)
    dummy_deployments = extract_param_value(input_parameters, "DummyDeployments", resource_pool, ssm_test_cache)
    for deployment_id in dummy_deployments:
        apigw_utils.delete_deployment(boto3_session, gateway_id, deployment_id)

    return True


@given(parsers.parse(cache_current_stage_deployment_id_expression))
@when(parsers.parse(cache_current_stage_deployment_id_expression))
@then(parsers.parse(cache_current_stage_deployment_id_expression))
def cache_current_stage_deployment_id(
        resource_pool, ssm_test_cache, boto3_session, cache_property, step_key, input_parameters
):
    gateway_id = extract_param_value(input_parameters, "RestApiGwId", resource_pool, ssm_test_cache)
    stage_name = extract_param_value(input_parameters, "RestStageName", resource_pool, ssm_test_cache)
    current_deployment_id = apigw_utils.get_stage(boto3_session, gateway_id, stage_name)['deploymentId']
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, current_deployment_id)


@given(parsers.parse(cache_current_wshttp_stage_deployment_id_expression))
@when(parsers.parse(cache_current_wshttp_stage_deployment_id_expression))
@then(parsers.parse(cache_current_wshttp_stage_deployment_id_expression))
def cache_current_wshttp_stage_deployment_id(
        resource_pool, ssm_test_cache, boto3_session, cache_property, step_key, input_parameters
):
    gateway_id = extract_param_value(input_parameters, "HttpWsApiGwId", resource_pool, ssm_test_cache)
    stage_name = extract_param_value(input_parameters, "HttpWsStageName", resource_pool, ssm_test_cache)
    current_deployment_id = apigw2_utils.get_stage(boto3_session, gateway_id, stage_name)['DeploymentId']
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, current_deployment_id)


@given(parsers.parse(update_current_stage_deployment_id_expression))
@when(parsers.parse(update_current_stage_deployment_id_expression))
@then(parsers.parse(update_current_stage_deployment_id_expression))
def update_current_stage_deployment_id(
        resource_pool, ssm_test_cache, boto3_session, cache_property, step_key, input_parameters
):
    gateway_id = extract_param_value(input_parameters, "RestApiGwId", resource_pool, ssm_test_cache)
    stage_name = extract_param_value(input_parameters, "RestStageName", resource_pool, ssm_test_cache)
    deployment_id = extract_param_value(input_parameters, "RestDeploymentId", resource_pool, ssm_test_cache)
    updated_deployment_id = apigw_utils.update_stage_deployment(
        boto3_session, gateway_id, stage_name, deployment_id
    )['deploymentId']
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, updated_deployment_id)


@given(parsers.parse(apply_dummy_deployment_to_stage_expression))
@when(parsers.parse(apply_dummy_deployment_to_stage_expression))
@then(parsers.parse(apply_dummy_deployment_to_stage_expression))
def apply_dummy_deployment_to_stage(
        resource_pool, ssm_test_cache, boto3_session, number, cache_property, step_key, input_parameters
):
    number = int(number) - 1
    gateway_id = extract_param_value(input_parameters, "RestApiGwId", resource_pool, ssm_test_cache)
    stage_name = extract_param_value(input_parameters, "RestStageName", resource_pool, ssm_test_cache)
    dummy_deployments = extract_param_value(input_parameters, "DummyDeployments", resource_pool, ssm_test_cache)
    dummy_deployment_id = dummy_deployments[number]
    previous_deployment_id = dummy_deployments[number - 1]
    apigw_utils.update_stage_deployment(boto3_session, gateway_id, stage_name, dummy_deployment_id)
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, previous_deployment_id)


@given(parsers.parse(apply_dummy_wshttp_deployment_to_stage_expression))
@when(parsers.parse(apply_dummy_wshttp_deployment_to_stage_expression))
@then(parsers.parse(apply_dummy_wshttp_deployment_to_stage_expression))
def apply_wshttp_dummy_deployment_to_stage(
        resource_pool, ssm_test_cache, boto3_session, number, cache_property, step_key, input_parameters
):
    number = int(number) - 1
    gateway_id = extract_param_value(input_parameters, "HttpWsApiGwId", resource_pool, ssm_test_cache)
    stage_name = extract_param_value(input_parameters, "HttpWsStageName", resource_pool, ssm_test_cache)
    dummy_deployments = extract_param_value(input_parameters, "DummyDeployments", resource_pool, ssm_test_cache)
    dummy_deployment_id = dummy_deployments[number]
    previous_deployment_id = dummy_deployments[number - 1]
    apigw2_utils.update_stage_deployment(boto3_session, gateway_id, stage_name, dummy_deployment_id)
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, previous_deployment_id)


@pytest.fixture(scope='function')
def rollback_throttling_settings(ssm_test_cache, boto3_session):
    yield
    logging.info('Rolling back API GW throttling settings...')
    logging.info(f'SSM test cache: {ssm_test_cache}')
    cache_before = ssm_test_cache['before']
    usage_plan_id = cache_before['RestApiGwUsagePlanId']
    rate_limit_before = cache_before['OldRateLimit']
    burst_limit_before = cache_before['OldBurstLimit']
    stage_name = cache_before.get('RestApiGwStageName')
    gateway_id = cache_before.get('RestApiGwId')

    actual_response = apigw_utils.set_throttling_settings(
        boto3_session, usage_plan_id, rate_limit_before, burst_limit_before, gateway_id, stage_name
    )
    assert rate_limit_before == actual_response['RateLimit']
    assert burst_limit_before == actual_response['BurstLimit']
    logging.info('Rollback is finished.')


@given(parsers.parse(cache_param_values_for_teardown_expression))
@when(parsers.parse(cache_param_values_for_teardown_expression))
@then(parsers.parse(cache_param_values_for_teardown_expression))
def cache_param_values_for_teardown(
        resource_pool, ssm_test_cache, rollback_throttling_settings, param_list, input_parameters, step_key
):
    extract_and_cache_param_values(input_parameters, param_list, resource_pool, ssm_test_cache, step_key)


@given(parsers.parse(cache_param_values_expression))
@when(parsers.parse(cache_param_values_expression))
@then(parsers.parse(cache_param_values_expression))
def cache_param_values(
        resource_pool, ssm_test_cache, param_list, input_parameters, step_key
):
    extract_and_cache_param_values(input_parameters, param_list, resource_pool, ssm_test_cache, step_key)


@given(parsers.parse(cache_throttling_settings_expression))
@when(parsers.parse(cache_throttling_settings_expression))
@then(parsers.parse(cache_throttling_settings_expression))
def cache_throttling_settings(
        ssm_test_cache, boto3_session, rate_limit_key, burst_limit_key, step_key
):
    cache_before = ssm_test_cache['before']
    usage_plan_id = cache_before['RestApiGwUsagePlanId']
    stage_name = cache_before.get('RestApiGwStageName')
    gateway_id = cache_before.get('RestApiGwId')

    throttling_settings = apigw_utils.get_throttling_settings(
        boto3_session, usage_plan_id, gateway_id, stage_name
    )

    put_to_ssm_test_cache(ssm_test_cache, step_key, rate_limit_key, throttling_settings['RateLimit'])
    put_to_ssm_test_cache(ssm_test_cache, step_key, burst_limit_key, throttling_settings['BurstLimit'])


@pytest.fixture(scope='function')
def default_route_throttling_settings(ssm_test_cache, boto3_session):
    default_route_throttling_settings = {}
    yield default_route_throttling_settings
    gateway_id = default_route_throttling_settings['HttpWsApiGwId']
    stage_name = default_route_throttling_settings['HttpWsStageName']
    backup_rate_limit = default_route_throttling_settings['BackupRateLimit']
    backup_burst_limit = default_route_throttling_settings['BackupBurstLimit']
    logging.info('Rolling back default route API GW throttling settings...')
    updated_stage_settings = apigw2_utils.update_default_throttling_settings(
        boto3_session, gateway_id, stage_name, backup_rate_limit, backup_burst_limit
    )['DefaultRouteSettings']
    assert updated_stage_settings['ThrottlingBurstLimit'] == backup_burst_limit
    assert updated_stage_settings['ThrottlingRateLimit'] == backup_rate_limit


@pytest.fixture(scope='function')
def route_throttling_settings(ssm_test_cache, boto3_session):
    route_throttling_settings = {}
    yield route_throttling_settings
    gateway_id = route_throttling_settings['HttpWsApiGwId']
    stage_name = route_throttling_settings['HttpWsStageName']
    route_key = route_throttling_settings['HttpWsRouteKey']
    backup_rate_limit = route_throttling_settings['BackupRateLimit']
    backup_burst_limit = route_throttling_settings['BackupBurstLimit']
    logging.info(f'Rolling back route {route_key} API GW throttling settings...')
    if backup_rate_limit and backup_burst_limit:
        updated_stage_settings = apigw2_utils.update_route_throttling_settings(
            boto3_session, gateway_id, stage_name, route_key, backup_rate_limit, backup_burst_limit
        )['RouteSettings'][route_key]
        assert updated_stage_settings['ThrottlingBurstLimit'] == backup_burst_limit
        assert updated_stage_settings['ThrottlingRateLimit'] == backup_rate_limit
    else:
        apigw2_client = client('apigatewayv2', boto3_session)
        apigw2_client.delete_route_settings(
            ApiId=gateway_id, StageName=stage_name, RouteKey=route_key
        )


@given(parsers.parse(cache_httpws_default_throttling_settings))
@when(parsers.parse(cache_httpws_default_throttling_settings))
@then(parsers.parse(cache_httpws_default_throttling_settings))
def cache_default_throttling_settings(
        resource_pool, ssm_test_cache, boto3_session, rate_limit_key, burst_limit_key, step_key, input_parameters
):
    gateway_id = extract_param_value(input_parameters, "HttpWsApiGwId", resource_pool, ssm_test_cache)
    stage_name = extract_param_value(input_parameters, "HttpWsStageName", resource_pool, ssm_test_cache)

    stage_default_settings = apigw2_utils.get_default_throttling_settings(
        boto3_session, gateway_id, stage_name
    )

    put_to_ssm_test_cache(ssm_test_cache, step_key, rate_limit_key, stage_default_settings['ThrottlingRateLimit'])
    put_to_ssm_test_cache(ssm_test_cache, step_key, burst_limit_key, stage_default_settings['ThrottlingBurstLimit'])


@given(parsers.parse(cache_httpws_route_throttling_settings))
@when(parsers.parse(cache_httpws_route_throttling_settings))
@then(parsers.parse(cache_httpws_route_throttling_settings))
def cache_route_throttling_settings(
        resource_pool, ssm_test_cache, boto3_session, rate_limit_key, burst_limit_key, step_key, input_parameters
):
    gateway_id = extract_param_value(input_parameters, "HttpWsApiGwId", resource_pool, ssm_test_cache)
    stage_name = extract_param_value(input_parameters, "HttpWsStageName", resource_pool, ssm_test_cache)
    route_key = extract_param_value(input_parameters, "HttpWsRouteKey", resource_pool, ssm_test_cache)

    stage_default_settings = apigw2_utils.get_route_throttling_settings(
        boto3_session, gateway_id, stage_name, route_key
    )

    put_to_ssm_test_cache(ssm_test_cache, step_key, rate_limit_key, stage_default_settings['ThrottlingRateLimit'])
    put_to_ssm_test_cache(ssm_test_cache, step_key, burst_limit_key, stage_default_settings['ThrottlingBurstLimit'])


@given(parsers.parse('prepare default route settings for teardown\n{input_parameters}'))
def prepare_default_route_settings_teardown(
        resource_pool, ssm_test_cache, default_route_throttling_settings, input_parameters
):
    gateway_id = extract_param_value(input_parameters, "HttpWsApiGwId", resource_pool, ssm_test_cache)
    stage_name = extract_param_value(input_parameters, "HttpWsStageName", resource_pool, ssm_test_cache)
    backup_rate_limit = extract_param_value(input_parameters, "BackupRateLimit", resource_pool, ssm_test_cache)
    backup_burst_limit = extract_param_value(input_parameters, "BackupBurstLimit", resource_pool, ssm_test_cache)
    # Prepare teardown
    default_route_throttling_settings['HttpWsApiGwId'] = gateway_id
    default_route_throttling_settings['HttpWsStageName'] = stage_name
    default_route_throttling_settings['BackupRateLimit'] = backup_rate_limit
    default_route_throttling_settings['BackupBurstLimit'] = backup_burst_limit


@given(parsers.parse('prepare route settings for teardown\n{input_parameters}'))
def prepare_route_settings_teardown(
        resource_pool, ssm_test_cache, route_throttling_settings, input_parameters
):
    gateway_id = extract_param_value(input_parameters, "HttpWsApiGwId", resource_pool, ssm_test_cache)
    stage_name = extract_param_value(input_parameters, "HttpWsStageName", resource_pool, ssm_test_cache)
    route_key = extract_param_value(input_parameters, "HttpWsRouteKey", resource_pool, ssm_test_cache)
    backup_rate_limit = extract_param_value(input_parameters, "BackupRateLimit", resource_pool, ssm_test_cache)
    backup_burst_limit = extract_param_value(input_parameters, "BackupBurstLimit", resource_pool, ssm_test_cache)
    # Prepare teardown
    route_throttling_settings['HttpWsApiGwId'] = gateway_id
    route_throttling_settings['HttpWsStageName'] = stage_name
    route_throttling_settings['HttpWsRouteKey'] = route_key
    route_throttling_settings['BackupRateLimit'] = backup_rate_limit
    route_throttling_settings['BackupBurstLimit'] = backup_burst_limit


@given(parsers.parse(get_api_key_and_perform_http_requests_expression))
@when(parsers.parse(get_api_key_and_perform_http_requests_expression))
@then(parsers.parse(get_api_key_and_perform_http_requests_expression))
def get_api_key_and_perform_http_requests(
        resource_pool, ssm_test_cache, boto3_session, key_id, count, delay, url, input_parameters
):
    api_key_id = extract_param_value(input_parameters, key_id, resource_pool, ssm_test_cache)
    request_url = extract_param_value(input_parameters, url, resource_pool, ssm_test_cache)
    request_count = int(count)
    request_delay = int(delay)
    apigw_client = client('apigateway', boto3_session)
    api_key = apigw_client.get_api_key(apiKey=api_key_id, includeValue=True)['value']
    while request_count > 0:
        response = requests.get(request_url, headers={'x-api-key': api_key})
        logging.info(f'Response status code: {response.status_code}')
        sleep(request_delay)
        request_count -= 1


@given(parsers.parse(get_api_key_and_invoke_lambda_to_perform_http_requests))
@when(parsers.parse(get_api_key_and_invoke_lambda_to_perform_http_requests))
@then(parsers.parse(get_api_key_and_invoke_lambda_to_perform_http_requests))
def get_api_key_and_invoke_lambda_to_perform_http_requests(
        resource_pool, boto3_session, api_key_id_ref, lambda_arn_ref, count, interval, ssm_test_cache
):
    cache_before = ssm_test_cache['before']
    lambda_arn = cache_before[lambda_arn_ref]
    api_key_id = cache_before[api_key_id_ref]
    request_count = int(count)
    request_interval = int(interval)
    apigw_client = client('apigateway', boto3_session)
    api_key = apigw_client.get_api_key(apiKey=api_key_id, includeValue=True)['value']
    payload = json.dumps({"api_key": api_key,
                          "request_interval": request_interval,
                          "request_count": request_count})
    logging.info(f'Invoke lambda {lambda_arn} ...')
    result = trigger_lambda(lambda_arn=lambda_arn,
                            payload=payload,
                            invocation_type=LambdaInvocationType.Event,
                            session=boto3_session)
    logging.info(f'Lambda StatusCode: {result["StatusCode"]}')
    logging.info(f'Lambda Request ID: {result["ResponseMetadata"]["RequestId"]}')


@given(parsers.parse(cache_vpc_endpoint_security_groups_map))
@when(parsers.parse(cache_vpc_endpoint_security_groups_map))
@then(parsers.parse(cache_vpc_endpoint_security_groups_map))
def cache_vpc_endpoint_security_groups_map(
        resource_pool, boto3_session, cache_property, step_key, ssm_test_cache
):
    gateway_id = ssm_test_cache['before']['RestApiGwId']
    apigw_client = client('apigateway', boto3_session)
    ec2_client = client('ec2', boto3_session)
    vpc_endpoint_ids = apigw_client.get_rest_api(restApiId=gateway_id)['endpointConfiguration']['vpcEndpointIds']
    vpc_endpoint_configs = ec2_client.describe_vpc_endpoints(VpcEndpointIds=vpc_endpoint_ids)['VpcEndpoints']
    vpc_endpoint_security_groups_map = {}
    for vpc_endpoint in vpc_endpoint_configs:
        vpc_endpoint_security_groups_map[vpc_endpoint['VpcEndpointId']] = vpc_endpoint['Groups']
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, vpc_endpoint_security_groups_map)
    logging.info(f'VPC endpoint Security Groups map: {repr(vpc_endpoint_security_groups_map)}')


call_http_endpoint_expression = 'call endpoint "{url}" "{number}" times with delay "{delay}" seconds ' \
                                'using method "{method}"' \
                                '\n{input_parameters}'


@given(parsers.parse(call_http_endpoint_expression))
@when(parsers.parse(call_http_endpoint_expression))
@then(parsers.parse(call_http_endpoint_expression))
def call_http_endpoint(
        resource_pool, ssm_test_cache, url, number, delay, method, input_parameters
):
    request_url = extract_param_value(input_parameters, url, resource_pool, ssm_test_cache)
    request_count = int(number)
    request_delay = int(delay)
    while request_count > 0:
        response = requests.request(method, request_url)
        logging.info(f'Send {method} request to {request_url}')
        logging.debug(f'Response status code: {response.status_code}')
        sleep(request_delay)
        request_count -= 1


call_ws_endpoint_expression = 'call ws endpoint "{url}" "{number}" times with delay "{delay}" seconds' \
                              '\n{input_parameters}'


@given(parsers.parse(call_ws_endpoint_expression))
@when(parsers.parse(call_ws_endpoint_expression))
@then(parsers.parse(call_ws_endpoint_expression))
def call_ws_endpoint(
        resource_pool, ssm_test_cache, url, number, delay, input_parameters
):
    ws_url = extract_param_value(input_parameters, url, resource_pool, ssm_test_cache)
    request_count = int(number)
    request_delay = int(delay)
    while request_count > 0:
        logging.info(f'Try ws handshake with {ws_url}')
        try:
            ws = create_connection(ws_url)
            logging.info('Connected successfully')
            ws.close()
        except WebSocketBadStatusException as e:
            logging.info(f'Handshake failed with {str(e.status_code)}')
        sleep(request_delay)
        request_count -= 1
