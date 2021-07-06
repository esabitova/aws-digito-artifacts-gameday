import logging
import time
import requests
from random import uniform
from time import sleep

from boto3 import Session
from botocore.config import Config
from botocore.exceptions import ClientError
from aws_requests_auth.aws_auth import AWSRequestsAuth

from .boto3_client_factory import client
from .common_test_utils import assert_https_status_code_200, assert_https_status_code_less_or_equal


def create_deployment(session: Session, gateway_id: str, description: str = '') -> dict:
    """
    Use gateway_id and description to create a dummy deployment resource for test
    :param session: The boto3 client session
    :param gateway_id: The string identifier of the associated RestApi
    :param description: The description of deployment
    :return: apigw_client.create_deployment response
    """
    apigw_client = client('apigateway', session)
    response = apigw_client.create_deployment(restApiId=gateway_id, description=description)
    assert_https_status_code_less_or_equal(201, response, f'Failed to create deployment: {description}, '
                                                          f'restApiId: {gateway_id}')
    return response


def delete_deployment(session: Session, gateway_id: str, deployment_id: str) -> bool:
    """
    Use gateway_id and deployment_id to delete dummy deployment resource
    :param session: The boto3 client session
    :param gateway_id: The string identifier of the associated RestApi
    :param deployment_id: The ID of deployment to delete
    :return: True if successful
    """
    apigw_client = client('apigateway', session)
    response = apigw_client.delete_deployment(restApiId=gateway_id, deploymentId=deployment_id)
    assert_https_status_code_less_or_equal(202, response, f'Failed to delete deploymentId: {deployment_id}, '
                                                          f'restApiId: {gateway_id}')
    return True


def get_stage(session: Session, gateway_id: str, stage_name: str) -> dict:
    """
    Use gateway_id and stage_name to get information about the Stage resource and return it as a dict
    :param session: The boto3 client session
    :param gateway_id: The string identifier of the associated RestApi
    :param stage_name: The name of the Stage resource to get information about
    :return: apigw_client.get_stage response
    """
    apigw_client = client('apigateway', session)
    response = apigw_client.get_stage(restApiId=gateway_id, stageName=stage_name)
    assert_https_status_code_200(response, f'Failed to perform get_stage with '
                                           f'restApiId: {gateway_id} and stageName: {stage_name}')
    return response


def update_stage_deployment(session: Session, gateway_id: str, stage_name: str, deployment_id: str) -> dict:
    """
    Use gateway_id, stage_name and deployment_id to update the Stage resource.
    :param session: The boto3 client session
    :param gateway_id: The string identifier of the associated RestApi
    :param stage_name: The name of the Stage resource to get information about
    :param deployment_id The Deployment ID to apply to Stage resource
    :return: apigw_client.update_stage response
    """
    apigw_client = client('apigateway', session)
    response = apigw_client.update_stage(
        restApiId=gateway_id,
        stageName=stage_name,
        patchOperations=[
            {
                'op': 'replace',
                'path': '/deploymentId',
                'value': deployment_id,
            },
        ]
    )
    assert_https_status_code_200(response, f'Failed to perform update_stage with restApiId: {gateway_id},'
                                           f' stageName: {stage_name} and deploymentId: {deployment_id}')
    return response


def update_usage_plan(
        session: Session, usage_plan_id: str, patch_operations: list,
        backoff_retries: int = 15, backoff_max_interval: int = 64, backoff_base_time: int = 2
) -> dict:
    config = Config(retries={'max_attempts': 0})
    apigw_client = session.client('apigateway', config=config)

    count = 1
    while count <= backoff_retries:
        try:
            logging.info(f'Making an API call update_usage_plan, attempt: {count} ...')
            response = apigw_client.update_usage_plan(usagePlanId=usage_plan_id, patchOperations=patch_operations)
            assert_https_status_code_200(response, f'Failed to update usage plan with id {usage_plan_id}')
            logging.info(f'API call update_usage_plan performed successfully on {count} attempt')
            return response
        except ClientError as error:
            if error.response['Error']['Code'] == 'TooManyRequestsException':
                interval: float = min(backoff_base_time * 2 ** count + round(uniform(-2, 2), 2), backoff_max_interval)
                logging.warning(f'TooManyRequestsException, slow it down with delay {interval} seconds ...')
                time.sleep(interval)
                count += 1
            else:
                logging.error(error)
                raise error

    raise Exception(f'Could not perform update_usage_plan successfully for {count - 1} times')


def set_throttling_settings(
        session: Session, usage_plan_id: str, rate_limit: float, burst_limit: int,
        gateway_id: str = None, stage_name: str = None, resource_path: str = '*', http_method: str = '*'
) -> dict:
    """
    Set throttling settings for provided usage_plan_id
    :param session: The boto3 client session
    :param usage_plan_id: The ID of REST API Gateway usage plan to be modified
    :param rate_limit: The value of throttling rate (requests per second)
    :param burst_limit: The value of throttling burst rate (requests per second)
    :param stage_name: (Optional) The name of the Stage which throttling settings should be applied to.
    :param gateway_id: (Optional) The ID of REST API Gateway. Required if Stage name is provided.
    :param resource_path: (Optional) The Resource Path which throttling settings should be applied to.
    :param http_method: (Optional) The HTTP method which throttling settings should be applied to.
    :return RateLimit: Actual value of throttling rate limit
    :return BurstLimit: Actual of throttling burst rate limit
    """
    output = {}
    patch_operations = [
        {
            'op': 'replace',
            'path': '/throttle/rateLimit',
            'value': str(rate_limit)
        },
        {
            'op': 'replace',
            'path': '/throttle/burstLimit',
            'value': str(burst_limit)
        }
    ]

    if stage_name:
        path: str = f'/apiStages/{gateway_id}:{stage_name}/throttle/{resource_path}/{http_method}'
        patch_operations[0]['path'], patch_operations[1]['path'] = f'{path}/rateLimit', f'{path}/burstLimit'
        updated_usage_plan = update_usage_plan(session, usage_plan_id, patch_operations)

        for stage in updated_usage_plan['apiStages']:
            if stage['apiId'] == gateway_id and stage['stage'] == stage_name:
                output['RateLimit'] = stage['throttle'][f'{resource_path}/{http_method}']['rateLimit']
                output['BurstLimit'] = stage['throttle'][f'{resource_path}/{http_method}']['burstLimit']
    else:
        updated_usage_plan = update_usage_plan(session, usage_plan_id, patch_operations)
        output['RateLimit'] = updated_usage_plan['throttle']['rateLimit']
        output['BurstLimit'] = updated_usage_plan['throttle']['burstLimit']

    return output


def get_throttling_settings(
        session: Session, usage_plan_id: str, gateway_id: str = None,
        stage_name: str = None, resource_path: str = '*', http_method: str = '*'
) -> dict:
    """
    Get throttling settings for provided usage_plan_id
    :param session: The boto3 client session
    :param usage_plan_id: The ID of REST API Gateway usage plan to be modified
    :param stage_name: (Optional) The name of the Stage which throttling settings should be get from.
    :param gateway_id: (Optional) The ID of REST API Gateway. Required if Stage name is provided.
    :param resource_path: (Optional) The Resource Path which throttling settings should be get from.
    :param http_method: (Optional) The HTTP method which throttling settings should be get from.
    :return RateLimit: Current value of throttling rate limit
    :return BurstLimit: Current value of throttling burst rate limit
    """
    apigw_client = client('apigateway', session)
    usage_plan = apigw_client.get_usage_plan(usagePlanId=usage_plan_id)

    if stage_name:
        for stage in usage_plan['apiStages']:
            if stage['apiId'] == gateway_id and stage['stage'] == stage_name:
                stage_found = True
                if 'throttle' in stage and f'{resource_path}/{http_method}' in stage['throttle']:
                    rate_limit: float = stage['throttle'][f'{resource_path}/{http_method}']['rateLimit']
                    burst_limit: int = stage['throttle'][f'{resource_path}/{http_method}']['burstLimit']
                else:
                    rate_limit: float = usage_plan['throttle']['rateLimit']
                    burst_limit: int = usage_plan['throttle']['burstLimit']
        if not stage_found:
            raise KeyError(f'Stage name {stage_name} not found in get_usage_plan response: {usage_plan}')
    else:
        rate_limit: float = usage_plan['throttle']['rateLimit']
        burst_limit: int = usage_plan['throttle']['burstLimit']

    return {'RateLimit': rate_limit,
            'BurstLimit': burst_limit}


def invoke_several_post_api_gw(boto3_session: Session,
                               api_key_id: str,
                               api_host: str,
                               api_url: str,
                               count: int,
                               interval: int):
    """
    Calls syncronously api gw with REST API 'POST' method, several times, and with a given delay.
    Authentication required
    :param boto3_session: The boto3 Session
    :param api_key_id: The ID of REST API Key
    :param api_host: host url for api-gw endpoint
    :param api_url: full endpoint url
    :param count: this is a number of api-gw calls
    :param interval: delay among calls
    """
    SEND_MESSAGE = {'message': 'mydino'}
    aws_credentials = boto3_session.get_credentials()
    aws_region = boto3_session.region_name
    apigw_client = client('apigateway', boto3_session)
    api_key = apigw_client.get_api_key(apiKey=api_key_id, includeValue=True)['value']
    api_auth = AWSRequestsAuth(aws_access_key=aws_credentials.access_key,
                               aws_secret_access_key=aws_credentials.secret_key,
                               aws_token=aws_credentials.token,
                               aws_host=api_host,
                               aws_region=aws_region,
                               aws_service='execute-api')
    while count > 0:
        logging.info(f'Sending post request to: {api_url}')
        requests.request('post', api_url, headers={'x-api-key': api_key}, auth=api_auth,
                         params=SEND_MESSAGE)
        sleep(interval)
        count -= 1
