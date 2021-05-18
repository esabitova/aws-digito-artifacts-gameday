import logging
import time
from random import uniform
from typing import Any, Callable

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

log = logging.getLogger()
log.setLevel(logging.INFO)


def check_limit_and_period(events, context):
    """
    Check if new values do not change usage plan by more than 50%
    :return: Evaluation result, old and new limits and periods
    """
    if 'RestApiGwUsagePlanId' not in events:
        raise KeyError('Requires RestApiGwUsagePlanId  in events')
    if 'RestApiGwQuotaLimit' not in events:
        raise KeyError('Requires RestApiGwQuotaLimit  in events')
    if 'RestApiGwQuotaPeriod' not in events:
        raise KeyError('Requires RestApiGwQuotaPeriod  in events')

    usage_plan_id = events['RestApiGwUsagePlanId']
    new_usage_plan_limit = events['RestApiGwQuotaLimit']
    new_usage_plan_period = events['RestApiGwQuotaPeriod']

    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    apigw_client = boto3.client('apigateway', config=config)

    log.debug(f'Getting limit and period from Plan {usage_plan_id} ...')
    apigw_usage_plan = apigw_client.get_usage_plan(usagePlanId=usage_plan_id)
    if not apigw_usage_plan['ResponseMetadata']['HTTPStatusCode'] == 200:
        log.error(f'Failed to get usage plan with id {usage_plan_id}, response is {apigw_usage_plan}')
        raise ValueError('Failed to get usage plan limit and period')

    current_usage_plan_limit = apigw_usage_plan["quota"]["limit"]
    current_usage_plan_period = apigw_usage_plan["quota"]["period"]
    log.debug(f'The converted period is {current_usage_plan_period}')
    choices = {'DAY': 1, 'WEEK': 7, 'MONTH': 30}
    divider_current = choices[current_usage_plan_period]
    divider_new = choices[new_usage_plan_period]

    converted_current_limit = int(apigw_usage_plan["quota"]["limit"]) / divider_current
    converted_new_limit = int(new_usage_plan_limit) / divider_new

    evaluation_message = "The converted current/new limits are " + str(converted_current_limit) + """/
                         """ + str(converted_new_limit)

    log.debug(evaluation_message)

    if abs(converted_current_limit - converted_new_limit) > converted_current_limit * 0.5:
        result = 'warning'
        exception = """Warning: The quota is going to be increased on more than 50%.
                    Please use smaller increments or use ForceExecution=True
                    parameter to disable validation. """ + evaluation_message
        raise AssertionError(exception)
    else:
        log.debug('Info: The quota is going to be increased not more than 50%')
        result = 'ok'

    return {"Result": result,
            "OriginalLimit": current_usage_plan_limit,
            "OriginalPeriod": current_usage_plan_period,
            "NewLimit": new_usage_plan_limit,
            "NewPeriod": new_usage_plan_period}


def set_limit_and_period(events, context):
    """
    Set usage plan limit and period
    :return: New limit and period
    """
    if 'RestApiGwUsagePlanId' not in events:
        raise KeyError('Requires RestApiGwUsagePlanId  in events')
    if 'RestApiGwQuotaLimit' not in events:
        raise KeyError('Requires RestApiGwQuotaLimit  in events')
    if 'RestApiGwQuotaPeriod' not in events:
        raise KeyError('Requires RestApiGwQuotaPeriod  in events')

    usage_plan_id = events['RestApiGwUsagePlanId']
    new_usage_plan_limit = events['RestApiGwQuotaLimit']
    new_usage_plan_period = events['RestApiGwQuotaPeriod']

    log.debug(f'Getting limit and period from Plan {usage_plan_id} ...')
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    apigw_client = boto3.client('apigateway', config=config)

    apigw_usage_plan = apigw_client.update_usage_plan(
        usagePlanId=usage_plan_id,
        patchOperations=[
            {
                'op': 'replace',
                'path': '/quota/limit',
                'value': new_usage_plan_limit
            },
            {
                'op': 'replace',
                'path': '/quota/period',
                'value': new_usage_plan_period
            }
        ])
    log.debug(f'The response from the API : {apigw_usage_plan}')
    if not apigw_usage_plan['ResponseMetadata']['HTTPStatusCode'] == 200:
        log.error(f'Failed to update usage plan with id {usage_plan_id}, response is {apigw_usage_plan}')
        raise ValueError('Failed to update usage plan limit and period')

    current_usage_plan_limit = apigw_usage_plan["quota"]["limit"]
    current_usage_plan_period = apigw_usage_plan["quota"]["period"]

    log.debug(f'The new limit is {current_usage_plan_limit}')
    log.debug(f'The new period is {current_usage_plan_period}')

    return {"Limit": current_usage_plan_limit,
            "Period": current_usage_plan_period}


def assert_https_status_code_200(response: dict, error_message: str) -> None:
    if not response['ResponseMetadata']['HTTPStatusCode'] == 200:
        raise ValueError(f'{error_message} Response is: {response}')


def execute_boto3_with_backoff(delegate: Callable[[Any], dict], **kwargs) -> dict:
    """
    Executes the given delegate with apigateway client parameter, handles TooManyRequestsException using
    exponential backoff algorithm with random jitter
    :param delegate: The delegate to execute (with boto3 function)
    :keyword args:
        retries: Number of maximum backoff retries
        max_interval: Maximum backoff interval in seconds
        base_time: Backoff base time
    :return: The output of the given function
    """
    backoff_retries: int = kwargs.get('retries', 15)
    backoff_max_interval: int = kwargs.get('max_interval', 64)
    backoff_base_time: int = kwargs.get('base_time', 2)
    apigw_client = boto3.client('apigateway')

    count = 1
    while count <= backoff_retries:
        try:
            log.info(f'Making an API call, attempt: {count} ...')
            response = delegate(apigw_client)
            assert_https_status_code_200(response, 'Failed to perform API call')
            log.info('API call performed successfully.')
            return response
        except ClientError as error:
            if error.response['Error']['Code'] == 'TooManyRequestsException':
                interval: float = min(backoff_base_time * 2 ** count + round(uniform(-2, 2), 2), backoff_max_interval)
                log.warning(f'TooManyRequestsException, slow it down with delay {interval} seconds ...')
                time.sleep(interval)
                count += 1
            else:
                log.error(error)
                raise error

    raise Exception(f'Failed to perform API call successfully for {count - 1} times.')


def get_service_quota(config: object, service_code: str, quota_code: str) -> dict:
    client = boto3.client('service-quotas', config=config)
    response = client.get_service_quota(ServiceCode=service_code, QuotaCode=quota_code)
    assert_https_status_code_200(response, f'Failed to perform get_service_quota with '
                                           f'ServiceCode: {service_code} and QuotaCode: {quota_code}')
    return response


def get_deployment(config: object, gateway_id: str, deployment_id: str) -> dict:
    client = boto3.client('apigateway', config=config)
    response = client.get_deployment(restApiId=gateway_id, deploymentId=deployment_id)
    assert_https_status_code_200(response, f'Failed to perform get_deployment with '
                                           f'restApiId: {gateway_id} and deploymentId: {deployment_id}')
    return response


def get_deployments(config: object, gateway_id: str, limit: int = 25, position: str = None) -> dict:
    client = boto3.client('apigateway', config=config)
    if not position:
        response = client.get_deployments(restApiId=gateway_id, limit=limit)
    else:
        response = client.get_deployments(restApiId=gateway_id, limit=limit, position=position)

    assert_https_status_code_200(response, f'Failed to perform get_deployments with restApiId: {gateway_id}')
    return response


def get_stage(config: object, gateway_id: str, stage_name: str) -> dict:
    client = boto3.client('apigateway', config=config)
    response = client.get_stage(restApiId=gateway_id, stageName=stage_name)
    assert_https_status_code_200(response, f'Failed to perform get_stage with '
                                           f'restApiId: {gateway_id} and stageName: {stage_name}')
    return response


def get_usage_plan(config: object, usage_plan_id: str) -> dict:
    client = boto3.client('apigateway', config=config)
    response = client.get_usage_plan(usagePlanId=usage_plan_id)
    assert_https_status_code_200(response, f'Failed to get usage plan with id {usage_plan_id}')
    return response


def update_usage_plan(usage_plan_id: str, patch_operations: list, retries: int = 15) -> dict:
    return execute_boto3_with_backoff(
        delegate=lambda x: x.update_usage_plan(
            usagePlanId=usage_plan_id,
            patchOperations=patch_operations
        ),
        retries=retries
    )


def find_deployment_id_for_update(events: dict, context: dict) -> dict:
    """
    Find deployment id for update
    """
    if 'RestApiGwId' not in events:
        raise KeyError('Requires RestApiGwId in events')

    if 'RestStageName' not in events:
        raise KeyError('Requires RestStageName in events')

    output: dict = {}
    gateway_id: str = events['RestApiGwId']
    stage_name: str = events['RestStageName']
    provided_deployment_id: str = events.get('RestDeploymentId', '')

    boto3_config: object = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    current_deployment_id = get_stage(boto3_config, gateway_id, stage_name)['deploymentId']
    output['OriginalDeploymentId'] = current_deployment_id

    if provided_deployment_id and provided_deployment_id == current_deployment_id:
        raise ValueError('Provided deployment ID and current deployment ID should not be the same')

    if provided_deployment_id:
        output['DeploymentIdToApply'] = get_deployment(boto3_config, gateway_id, provided_deployment_id)['id']
        return output

    deployment_items = get_deployments(boto3_config, gateway_id, 500)['items']
    if len(deployment_items) == 1 and deployment_items[0]['id'] == current_deployment_id:
        raise ValueError(f'There are no deployments found to apply in RestApiGateway ID: {gateway_id}, '
                         f'except current deployment ID: {current_deployment_id}')

    current_deployment_creation_date = get_deployment(boto3_config, gateway_id, current_deployment_id)['createdDate']
    deployment_items.sort(key=lambda x: x['createdDate'], reverse=True)
    for item in deployment_items:
        if item['createdDate'] < current_deployment_creation_date and item['id'] != current_deployment_id:
            output['DeploymentIdToApply'] = item['id']
            return output

    raise ValueError(f'Could not find any existing deployment which has createdDate less than current deployment ID: '
                     f'{current_deployment_id}, with createdDate: {current_deployment_creation_date}')


def update_deployment(events: dict, context: dict) -> dict:
    """
    Apply RestDeploymentId to provided RestStageName
    """
    if 'RestApiGwId' not in events:
        raise KeyError('Requires RestApiGwId in events')

    if 'RestStageName' not in events:
        raise KeyError('Requires RestStageName in events')

    if 'RestDeploymentId' not in events:
        raise KeyError('Requires RestDeploymentId in events')

    gateway_id: str = events['RestApiGwId']
    stage_name: str = events['RestStageName']
    deployment_id: str = events['RestDeploymentId']

    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    client = boto3.client('apigateway', config=config)
    response = client.update_stage(
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

    return {'DeploymentIdNewValue': response['deploymentId'],
            'StageName': response['stageName']}


def validate_throttling_config(events: dict, context: dict) -> dict:
    if 'RestApiGwUsagePlanId' not in events:
        raise KeyError('Requires RestApiGwUsagePlanId in events')

    if 'RestApiGwThrottlingRate' not in events:
        raise KeyError('Requires RestApiGwThrottlingRate in events')

    if 'RestApiGwThrottlingBurst' not in events:
        raise KeyError('Requires RestApiGwThrottlingBurst in events')

    if 'RestApiGwStageName' in events and events['RestApiGwStageName']:
        if 'RestApiGwId' not in events:
            raise KeyError('Requires RestApiGwId in events')
        if not events['RestApiGwId']:
            raise KeyError('RestApiGwId should not be empty')

    usage_plan_id: str = events['RestApiGwUsagePlanId']
    new_rate_limit: float = float(events['RestApiGwThrottlingRate'])
    new_burst_limit: int = int(events['RestApiGwThrottlingBurst'])
    gateway_id: str = events.get('RestApiGwId')
    stage_name: str = events.get('RestApiGwStageName')
    resource_path: str = events.get('RestApiGwResourcePath', '*')
    http_method: str = events.get('RestApiGwHttpMethod', '*')

    boto3_config: object = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    current_usage_plan: dict = get_usage_plan(boto3_config, usage_plan_id)

    if stage_name:
        stage_found = False
        for stage in current_usage_plan['apiStages']:
            if stage['apiId'] == gateway_id and stage['stage'] == stage_name:
                stage_found = True
                if 'throttle' in stage and f'{resource_path}/{http_method}' in stage['throttle']:
                    original_rate_limit: float = stage['throttle'][f'{resource_path}/{http_method}']['rateLimit']
                    original_burst_limit: int = stage['throttle'][f'{resource_path}/{http_method}']['burstLimit']
                else:
                    original_rate_limit: float = current_usage_plan['throttle']['rateLimit']
                    original_burst_limit: int = current_usage_plan['throttle']['burstLimit']
        if not stage_found:
            raise KeyError(f'Stage name {stage_name} not found in get_usage_plan response: {current_usage_plan}')
    else:
        original_rate_limit: float = current_usage_plan['throttle']['rateLimit']
        original_burst_limit: int = current_usage_plan['throttle']['burstLimit']

    if abs(new_burst_limit - original_burst_limit) > original_burst_limit * 0.5:
        raise ValueError('Burst rate limit is going to be changed more than 50%, please use smaller increments or use '
                         'ForceExecution parameter to disable validation')

    if abs(new_rate_limit - original_rate_limit) > original_rate_limit * 0.5:
        raise ValueError('Rate limit is going to be changed more than 50%, please use smaller increments or use '
                         'ForceExecution parameter to disable validation')

    original_rate_limit = int(original_rate_limit)

    return {'OriginalRateLimit': original_rate_limit,
            'OriginalBurstLimit': original_burst_limit}


def set_throttling_config(events: dict, context: dict) -> dict:
    if 'RestApiGwUsagePlanId' not in events:
        raise KeyError('Requires RestApiGwUsagePlanId in events')

    if 'RestApiGwThrottlingRate' not in events:
        raise KeyError('Requires RestApiGwThrottlingRate in events')

    if 'RestApiGwThrottlingBurst' not in events:
        raise KeyError('Requires RestApiGwThrottlingBurst in events')

    if 'RestApiGwStageName' in events and events['RestApiGwStageName']:
        if 'RestApiGwId' not in events:
            raise KeyError('Requires RestApiGwId in events')
        if not events['RestApiGwId']:
            raise KeyError('RestApiGwId should not be empty')

    usage_plan_id: str = events['RestApiGwUsagePlanId']
    new_rate_limit: float = float(events['RestApiGwThrottlingRate'])
    new_burst_limit: int = int(events['RestApiGwThrottlingBurst'])
    gateway_id: str = events.get('RestApiGwId')
    stage_name: str = events.get('RestApiGwStageName')
    resource_path: str = events.get('RestApiGwResourcePath', '*')
    http_method: str = events.get('RestApiGwHttpMethod', '*')

    output: dict = {}
    quota_rate_limit_code: str = 'L-8A5B8E43'
    quota_burst_limit_code: str = 'L-CDF5615A'
    patch_operations: list = [
        {
            'op': 'replace',
            'path': '/throttle/rateLimit',
            'value': str(new_rate_limit)
        },
        {
            'op': 'replace',
            'path': '/throttle/burstLimit',
            'value': str(new_burst_limit)
        }
    ]

    boto3_config: object = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    quota_rate_limit: float = get_service_quota(boto3_config, 'apigateway', quota_rate_limit_code)['Quota']['Value']
    quota_burst_limit: float = get_service_quota(boto3_config, 'apigateway', quota_burst_limit_code)['Quota']['Value']

    if new_rate_limit > quota_rate_limit:
        raise ValueError(f'Given value of RestApiGwThrottlingRate: {new_rate_limit}, can not be more than '
                         f'service quota Throttle rate: {quota_rate_limit}')

    if new_burst_limit > quota_burst_limit:
        raise ValueError(f'Given value of RestApiGwThrottlingBurst: {new_burst_limit}, can not be more than '
                         f'service quota Throttle burst rate: {quota_burst_limit}')
    if stage_name:
        path: str = f'/apiStages/{gateway_id}:{stage_name}/throttle/{resource_path}/{http_method}'
        patch_operations[0]['path'], patch_operations[1]['path'] = f'{path}/rateLimit', f'{path}/burstLimit'
        updated_usage_plan = update_usage_plan(usage_plan_id, patch_operations)

        for stage in updated_usage_plan['apiStages']:
            if stage['apiId'] == gateway_id and stage['stage'] == stage_name:
                output['RateLimit'] = stage['throttle'][f'{resource_path}/{http_method}']['rateLimit']
                output['BurstLimit'] = stage['throttle'][f'{resource_path}/{http_method}']['burstLimit']
    else:
        updated_usage_plan = update_usage_plan(usage_plan_id, patch_operations)
        output['RateLimit'] = updated_usage_plan['throttle']['rateLimit']
        output['BurstLimit'] = updated_usage_plan['throttle']['burstLimit']

    output['RateLimit'] = int(output['RateLimit'])

    return output
