import logging

import boto3
from botocore.config import Config

log = logging.getLogger()
log.setLevel(logging.DEBUG)


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

    if (abs(converted_current_limit - converted_new_limit) > converted_current_limit * 0.5):
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


def get_deployment(gateway_id: str, deployment_id: str) -> dict:
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    client = boto3.client('apigateway', config=config)
    deployment = client.get_deployment(restApiId=gateway_id, deploymentId=deployment_id)
    if not deployment['ResponseMetadata']['HTTPStatusCode'] == 200:
        log.error(f'Failed to perform get_deployment with restApiId {gateway_id} and \
        deploymentId {deployment_id},response is {deployment}')
        raise ValueError('Failed to perform get_deployment')
    return deployment


def get_deployments(gateway_id: str, limit: int = 25, position: str = '') -> dict:
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    client = boto3.client('apigateway', config=config)
    if not position:
        deployments = client.get_deployments(restApiId=gateway_id, limit=limit)
    else:
        deployments = client.get_deployments(restApiId=gateway_id, limit=limit, position=position)
    if not deployments['ResponseMetadata']['HTTPStatusCode'] == 200:
        log.error(f'Failed to perform get_deployments with restApiId: {gateway_id},response is: {deployments}')
        raise ValueError('Failed to perform get_deployment')
    return deployments


def get_stage(gateway_id: str, stage_name: str) -> dict:
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    client = boto3.client('apigateway', config=config)
    stage = client.get_stage(restApiId=gateway_id, stageName=stage_name)
    if not stage['ResponseMetadata']['HTTPStatusCode'] == 200:
        log.error(f'Failed to perform get_deployment with restApiId {gateway_id} and \
        stageName {stage_name},response is {stage}')
        raise ValueError('Failed to perform get_stage')
    return stage


def find_previous_deployment_if_not_provided(events: dict, context: dict) -> dict:
    """
    Find previous deployment if not provided
    """
    if 'RestApiGwId' not in events or 'RestStageName' not in events:
        raise KeyError('Requires RestApiGwId and RestStageName in events')

    gateway_id: str = events['RestApiGwId']
    stage_name: str = events['RestStageName']
    provided_deployment_id: str = events.get('RestDeploymentId', '')
    output = {}

    current_deployment_id = get_stage(gateway_id, stage_name)['deploymentId']
    output['OriginalDeploymentId'] = current_deployment_id

    if provided_deployment_id and provided_deployment_id == current_deployment_id:
        raise ValueError('Provided deployment ID and current deployment ID should not be the same')

    if provided_deployment_id:
        output['DeploymentIdToApply'] = get_deployment(gateway_id, provided_deployment_id)['id']
        return output

    current_deployment_creation_date = get_deployment(gateway_id, current_deployment_id)['createdDate']
    deployment_items = get_deployments(gateway_id, 500)['items']
    if len(deployment_items) == 1 and deployment_items[0]['id'] == current_deployment_id:
        raise ValueError(f'There are no deployments found to apply in RestApiGateway ID: {gateway_id},\
        except current deployment ID: {current_deployment_id}')

    deployment_items.sort(key=lambda x: x['createdDate'], reverse=True)
    for item in deployment_items:
        if item['createdDate'] < current_deployment_creation_date and item['id'] != current_deployment_id:
            output['DeploymentIdToApply'] = item['id']
            return output

    raise ValueError(f'Could not find any existing deployment which has createdDate less than current deployment ID: \
      {current_deployment_id}, with createdDate: {current_deployment_creation_date}')


def update_deployment(events: dict, context: dict) -> dict:
    """
    Apply RestDeploymentId to provided RestStageName
    """
    if 'RestApiGwId' not in events or 'RestStageName' not in events or 'RestDeploymentId' not in events:
        raise KeyError('Requires RestApiGwId, RestStageName and DeploymentId in events')

    output = {}
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
    output['DeploymentIdNewValue'] = response['deploymentId']

    return output
