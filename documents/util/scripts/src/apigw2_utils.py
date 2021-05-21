import logging

import boto3
from botocore.config import Config

log = logging.getLogger()
log.setLevel(logging.DEBUG)


def assert_https_status_code_200(response: dict, error_message: str) -> None:
    if not response['ResponseMetadata']['HTTPStatusCode'] == 200:
        raise ValueError(f'{error_message} Response is: {response}')


def get_deployment(gateway_id: str, deployment_id: str) -> dict:
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    client = boto3.client('apigatewayv2', config=config)
    response = client.get_deployment(ApiId=gateway_id, DeploymentId=deployment_id)
    assert_https_status_code_200(response, f'Failed to perform get_deployment with '
                                           f'ApiId: {gateway_id} and DeploymentId: {deployment_id}')
    return response


def get_deployments(gateway_id: str, limit: str = '25') -> dict:
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    client = boto3.client('apigatewayv2', config=config)
    response = client.get_deployments(ApiId=gateway_id, MaxResults=limit)
    assert_https_status_code_200(response, f'Failed to perform get_deployments with ApiId: {gateway_id}')
    return response


def get_stage(gateway_id: str, stage_name: str) -> dict:
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    client = boto3.client('apigatewayv2', config=config)
    response = client.get_stage(ApiId=gateway_id, StageName=stage_name)
    assert_https_status_code_200(response, f'Failed to perform get_stage with '
                                           f'ApiId: {gateway_id} and StageName: {stage_name}')
    return response


def find_deployment_id_for_update(events: dict, context: dict) -> dict:
    """
    Find deployment id for update
    """
    if 'HttpWsApiGwId' not in events:
        raise KeyError('Requires HttpWsApiGwId in events')

    if 'HttpWsStageName' not in events:
        raise KeyError('Requires HttpWsStageName in events')

    output: dict = {}
    gateway_id: str = events['HttpWsApiGwId']
    stage_name: str = events['HttpWsStageName']
    provided_deployment_id: str = events.get('HttpWsDeploymentId', '')

    current_deployment_id = get_stage(gateway_id, stage_name)['DeploymentId']
    output['OriginalDeploymentId'] = current_deployment_id

    if provided_deployment_id and provided_deployment_id == current_deployment_id:
        raise ValueError('Provided deployment ID and current deployment ID should not be the same')

    if provided_deployment_id:
        output['DeploymentIdToApply'] = get_deployment(gateway_id, provided_deployment_id)['DeploymentId']
        return output

    deployment_items = get_deployments(gateway_id, '500')['Items']
    if len(deployment_items) == 1 and deployment_items[0]['DeploymentId'] == current_deployment_id:
        raise ValueError(f'There are no deployments found to apply in ApiGateway ID: {gateway_id}, '
                         f'except current deployment ID: {current_deployment_id}')

    current_deployment_creation_date = get_deployment(gateway_id, current_deployment_id)['CreatedDate']
    deployment_items.sort(key=lambda x: x['CreatedDate'], reverse=True)
    for item in deployment_items:
        if item['CreatedDate'] < current_deployment_creation_date and item['DeploymentId'] != current_deployment_id:
            output['DeploymentIdToApply'] = item['DeploymentId']
            return output

    raise ValueError(f'Could not find any existing deployment which has createdDate less than current deployment ID: '
                     f'{current_deployment_id}, with createdDate: {current_deployment_creation_date}')


def update_deployment(events: dict, context: dict) -> dict:
    """
    Apply DeploymentId to provided StageName
    """
    if 'HttpWsApiGwId' not in events:
        raise KeyError('Requires HttpWsApiGwId in events')

    if 'HttpWsStageName' not in events:
        raise KeyError('Requires HttpWsStageName in events')

    if 'HttpWsDeploymentId' not in events:
        raise KeyError('Requires HttpWsDeploymentId in events')

    gateway_id: str = events['HttpWsApiGwId']
    stage_name: str = events['HttpWsStageName']
    deployment_id: str = events['HttpWsDeploymentId']

    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    client = boto3.client('apigatewayv2', config=config)
    response = client.update_stage(
        ApiId=gateway_id,
        StageName=stage_name,
        DeploymentId=deployment_id
    )
    assert_https_status_code_200(response, f'Failed to perform update_stage with ApiId: {gateway_id},'
                                           f' StageName: {stage_name} and DeploymentId: {deployment_id}')

    return {'DeploymentIdNewValue': response['DeploymentId'],
            'StageName': response['StageName']}


def validate_auto_deploy(events: dict, context: dict) -> bool:
    """
    Validate that AutoDeploy is turned off for stage StageName
    """
    if 'HttpWsApiGwId' not in events:
        raise KeyError('Requires HttpWsApiGwId in events')

    if 'HttpWsStageName' not in events:
        raise KeyError('Requires HttpWsStageName in events')

    gateway_id: str = events['HttpWsApiGwId']
    stage_name: str = events['HttpWsStageName']

    response = get_stage(gateway_id, stage_name)

    if 'AutoDeploy' in response and response['AutoDeploy']:
        raise ValueError('AutoDeploy must be turned off to update deployment manually')
    return True


def validate_throttling_config(events: dict, context: dict) -> dict:
    if 'HttpWsThrottlingRate' not in events:
        raise KeyError('Requires HttpWsThrottlingRate in events')

    if 'HttpWsThrottlingBurst' not in events:
        raise KeyError('Requires HttpWsThrottlingBurst in events')

    if 'HttpWsApiGwId' not in events:
        raise KeyError('Requires HttpWsApiGwId in events')

    if 'HttpWsStageName' not in events:
        raise KeyError('Requires HttpWsStageName in events')

    new_rate_limit: float = float(events['HttpWsThrottlingRate'])
    new_burst_limit: int = int(events['HttpWsThrottlingBurst'])
    gateway_id: str = events.get('HttpWsApiGwId')
    stage_name: str = events.get('HttpWsStageName')
    route_key: str = events.get('HttpWsRouteKey', '*')

    stage = get_stage(gateway_id, stage_name)
    if route_key != '*':
        if route_key in stage['RouteSettings']:
            original_rate_limit: float = stage['RouteSettings'][route_key].get('ThrottlingRateLimit', 0.0)
            original_burst_limit: int = stage['RouteSettings'][route_key].get('ThrottlingBurstLimit', 0)
        else:
            original_rate_limit: float = 0.0
            original_burst_limit: int = 0
    else:
        original_rate_limit: float = stage['DefaultRouteSettings'].get('ThrottlingRateLimit', 0.0)
        original_burst_limit: int = stage['DefaultRouteSettings'].get('ThrottlingBurstLimit', 0)

    if original_burst_limit and abs(new_burst_limit - original_burst_limit) > original_burst_limit * 0.5:
        raise ValueError('Burst rate limit is going to be changed more than 50%, please use smaller increments or use '
                         'ForceExecution parameter to disable validation')

    if original_rate_limit and abs(new_rate_limit - original_rate_limit) > original_rate_limit * 0.5:
        raise ValueError('Rate limit is going to be changed more than 50%, please use smaller increments or use '
                         'ForceExecution parameter to disable validation')

    original_rate_limit = int(original_rate_limit)

    return {'OriginalRateLimit': original_rate_limit,
            'OriginalBurstLimit': original_burst_limit}


def get_service_quota(config: object, service_code: str, quota_code: str) -> dict:
    client = boto3.client('service-quotas', config=config)
    response = client.get_service_quota(ServiceCode=service_code, QuotaCode=quota_code)
    assert_https_status_code_200(response, f'Failed to perform get_service_quota with '
                                           f'ServiceCode: {service_code} and QuotaCode: {quota_code}')
    return response


def set_throttling_config(events: dict, context: dict) -> dict:
    if 'HttpWsApiGwId' not in events:
        raise KeyError('Requires HttpWsApiGwId in events')

    if 'HttpWsThrottlingRate' not in events:
        raise KeyError('Requires HttpWsThrottlingRate in events')

    if 'HttpWsThrottlingBurst' not in events:
        raise KeyError('Requires HttpWsThrottlingBurst in events')

    if 'HttpWsStageName' not in events:
        raise KeyError('Requires HttpWsStageName in events')

    new_rate_limit: float = float(events['HttpWsThrottlingRate'])
    new_burst_limit: int = int(events['HttpWsThrottlingBurst'])
    gateway_id: str = events.get('HttpWsApiGwId')
    stage_name: str = events.get('HttpWsStageName')
    route_key: str = events.get('HttpWsRouteKey', '*')

    output: dict = {}
    quota_rate_limit_code: str = 'L-8A5B8E43'
    quota_burst_limit_code: str = 'L-CDF5615A'

    boto3_config: object = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    apigw2_client = boto3.client('apigatewayv2', config=boto3_config)
    quota_rate_limit: float = get_service_quota(boto3_config, 'apigateway', quota_rate_limit_code)['Quota']['Value']
    quota_burst_limit: float = get_service_quota(boto3_config, 'apigateway', quota_burst_limit_code)['Quota']['Value']

    if new_rate_limit > quota_rate_limit:
        raise ValueError(f'Given value of HttpWsThrottlingRate: {new_rate_limit}, can not be more than '
                         f'service quota Throttle rate: {quota_rate_limit}')

    if new_burst_limit > quota_burst_limit:
        raise ValueError(f'Given value of HttpWsThrottlingBurst: {new_burst_limit}, can not be more than '
                         f'service quota Throttle burst rate: {quota_burst_limit}')

    stage = get_stage(gateway_id, stage_name)

    if route_key != '*':
        stage_route_settings = stage['RouteSettings']
        if route_key not in stage_route_settings:
            stage_route_settings[route_key] = {}
        stage_route_settings[route_key]['ThrottlingRateLimit'] = new_rate_limit
        stage_route_settings[route_key]['ThrottlingBurstLimit'] = new_burst_limit

        response = apigw2_client.update_stage(
            ApiId=gateway_id, StageName=stage_name, RouteSettings=stage_route_settings
        )
        output['RateLimit'] = response['RouteSettings'][route_key]['ThrottlingRateLimit']
        output['BurstLimit'] = response['RouteSettings'][route_key]['ThrottlingBurstLimit']

    else:
        default_route_settings = {
            'ThrottlingRateLimit': new_rate_limit,
            'ThrottlingBurstLimit': new_burst_limit
        }
        response = apigw2_client.update_stage(
            ApiId=gateway_id, StageName=stage_name, DefaultRouteSettings=default_route_settings
        )
        output['RateLimit'] = response['DefaultRouteSettings']['ThrottlingRateLimit']
        output['BurstLimit'] = response['DefaultRouteSettings']['ThrottlingBurstLimit']

    output['RateLimit'] = int(output['RateLimit'])
    return output
