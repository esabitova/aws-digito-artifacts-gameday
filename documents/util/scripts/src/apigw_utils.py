import json
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
    if apigw_usage_plan['ResponseMetadata']['HTTPStatusCode'] != 200:
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

    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    apigw_client = boto3.client('apigateway', config=config)

    apigw_usage_plan = apigw_client.update_usage_plan(
        usagePlanId=usage_plan_id,
        patchOperations=[
            {
                'op': 'replace',
                'path': '/quota/limit',
                'value': str(new_usage_plan_limit)
            },
            {
                'op': 'replace',
                'path': '/quota/period',
                'value': new_usage_plan_period
            }
        ])
    log.debug(f'The response from the API : {apigw_usage_plan}')
    if apigw_usage_plan['ResponseMetadata']['HTTPStatusCode'] != 200:
        log.error(f'Failed to update usage plan with id {usage_plan_id}, response is {apigw_usage_plan}')
        raise ValueError('Failed to update usage plan limit and period')

    wait_limit_and_period_updated(events, None)

    return {"Limit": apigw_usage_plan["quota"]["limit"],
            "Period": apigw_usage_plan["quota"]["period"]}


def wait_limit_and_period_updated(events, context):
    expected_quota_limit: int = events['RestApiGwQuotaLimit']
    expected_quota_period: str = events['RestApiGwQuotaPeriod']
    max_retries: int = events.get('MaxRetries', 40)
    timeout: int = events.get('Timeout', 15)
    while max_retries > 0:
        actual_throttling_config = get_throttling_config(events, None)
        actual_quota_limit = actual_throttling_config['QuotaLimit']
        actual_quota_period = actual_throttling_config['QuotaPeriod']
        if actual_quota_limit == expected_quota_limit and actual_quota_period == expected_quota_period:
            return
        log.info(f'Waiting for expected values: '
                 f'[QuotaLimit: {expected_quota_limit}, QuotaPeriod: {expected_quota_period}], '
                 f'actual values: [QuotaLimit: {actual_quota_limit}, QuotaPeriod: {actual_quota_period}]')
        max_retries -= 1
        time.sleep(timeout)

    raise TimeoutError('Error to wait for QuotaLimit and QuotaPeriod update. Maximum timeout exceeded!')


def assert_https_status_code_200(response: dict, error_message: str) -> None:
    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
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
            log.debug(f'Making an API call, attempt: {count} ...')
            response = delegate(apigw_client)
            assert_https_status_code_200(response, 'Failed to perform API call')
            log.debug('API call performed successfully.')
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


def get_deployments(config: object, gateway_id: str, limit: int = 25) -> dict:
    client = boto3.client('apigateway', config=config)
    response = client.get_deployments(restApiId=gateway_id, limit=limit)
    assert_https_status_code_200(response, f'Failed to perform get_deployments with restApiId: {gateway_id}')
    return response


def get_stage(config: object, gateway_id: str, stage_name: str) -> dict:
    client = boto3.client('apigateway', config=config)
    response = client.get_stage(restApiId=gateway_id, stageName=stage_name)
    assert_https_status_code_200(response, f'Failed to perform get_stage with '
                                           f'restApiId: {gateway_id} and stageName: {stage_name}')
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


def get_throttling_config(events: dict, context: dict) -> dict:
    if 'RestApiGwUsagePlanId' not in events:
        raise KeyError('Requires RestApiGwUsagePlanId in events')

    if 'RestApiGwStageName' in events and events['RestApiGwStageName']:
        if 'RestApiGwId' not in events:
            raise KeyError('Requires RestApiGwId in events')
        if not events['RestApiGwId']:
            raise KeyError('RestApiGwId should not be empty')

    usage_plan_id: str = events['RestApiGwUsagePlanId']
    gateway_id: str = events.get('RestApiGwId')
    stage_name: str = events.get('RestApiGwStageName')
    resource_path: str = events.get('RestApiGwResourcePath', '*')
    http_method: str = events.get('RestApiGwHttpMethod', '*')

    # Need to have it here for rollback case to overcame issue DIG-853 with get_inputs_from_ssm_execution
    if (stage_name and stage_name.startswith('{{')) and (gateway_id and gateway_id.startswith('{{')):
        gateway_id = stage_name = None
    resource_path = '*' if resource_path.startswith('{{') else resource_path
    http_method = '*' if http_method.startswith('{{') else http_method

    config: object = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    client = boto3.client('apigateway', config=config)
    usage_plan = client.get_usage_plan(usagePlanId=usage_plan_id)
    assert_https_status_code_200(usage_plan, f'Failed to get usage plan with id {usage_plan_id}')

    if stage_name:
        stage_found = False
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

    return {'RateLimit': int(rate_limit),
            'BurstLimit': burst_limit,
            'QuotaLimit': usage_plan['quota']['limit'],
            'QuotaPeriod': usage_plan['quota']['period']}


def validate_throttling_config(events: dict, context: dict) -> dict:
    if 'RestApiGwThrottlingRate' not in events:
        raise KeyError('Requires RestApiGwThrottlingRate in events')

    if 'RestApiGwThrottlingBurst' not in events:
        raise KeyError('Requires RestApiGwThrottlingBurst in events')

    new_rate_limit: int = int(events['RestApiGwThrottlingRate'])
    new_burst_limit: int = int(events['RestApiGwThrottlingBurst'])

    usage_plan: dict = get_throttling_config(events, None)
    original_rate_limit: int = usage_plan['RateLimit']
    original_burst_limit: int = usage_plan['BurstLimit']

    if original_burst_limit and abs(new_burst_limit - original_burst_limit) > original_burst_limit * 0.5:
        raise ValueError('Burst rate limit is going to be changed more than 50%, please use smaller increments or use '
                         'ForceExecution parameter to disable validation')

    if original_rate_limit and abs(new_rate_limit - original_rate_limit) > original_rate_limit * 0.5:
        raise ValueError('Rate limit is going to be changed more than 50%, please use smaller increments or use '
                         'ForceExecution parameter to disable validation')

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
    validate_quota_limits: bool = events.get('ValidateQuotaLimits', True)

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

    # Need to have it here for rollback case to overcame issue DIG-853 with get_inputs_from_ssm_execution
    if (stage_name and stage_name.startswith('{{')) and (gateway_id and gateway_id.startswith('{{')):
        gateway_id = stage_name = None
    resource_path = '*' if resource_path.startswith('{{') else resource_path
    http_method = '*' if http_method.startswith('{{') else http_method

    boto3_config: object = Config(retries={'max_attempts': 20, 'mode': 'standard'})

    if validate_quota_limits:
        quota_rate_limit: float = get_service_quota(
            boto3_config, 'apigateway', quota_rate_limit_code)['Quota']['Value']
        quota_burst_limit: float = get_service_quota(
            boto3_config, 'apigateway', quota_burst_limit_code)['Quota']['Value']

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
    wait_throttling_config_updated(events, None)

    return output


def wait_throttling_config_updated(events: dict, context: dict) -> None:
    expected_rate_limit: int = int(events['RestApiGwThrottlingRate'])
    expected_burst_limit: int = int(events['RestApiGwThrottlingBurst'])
    max_retries: int = events.get('MaxRetries', 40)
    timeout: int = events.get('Timeout', 15)
    while max_retries > 0:
        actual_throttling_config = get_throttling_config(events, None)
        actual_rate_limit = actual_throttling_config['RateLimit']
        actual_burst_limit = actual_throttling_config['BurstLimit']
        if actual_rate_limit == expected_rate_limit and actual_burst_limit == expected_burst_limit:
            return
        log.info(f'Waiting for expected values: [RateLimit: {expected_rate_limit}, BurstLimit: {expected_burst_limit}],'
                 f' actual values: [RateLimit: {actual_rate_limit}, BurstLimit: {actual_burst_limit}]')
        max_retries -= 1
        time.sleep(timeout)

    raise TimeoutError('Error to wait for throttling config update. Maximum timeout exceeded!')


def assert_inputs_before_throttling_rollback(events: dict, context: dict) -> None:
    usage_plan_id: str = events['RestApiGwUsagePlanId']
    gateway_id: str = events.get('RestApiGwId')
    stage_name: str = events.get('RestApiGwStageName')
    resource_path: str = events.get('RestApiGwResourcePath', '*')
    http_method: str = events.get('RestApiGwHttpMethod', '*')

    original_usage_plan_id: str = events['OriginalRestApiGwUsagePlanId']
    original_gateway_id: str = events.get('OriginalRestApiGwId')
    original_stage_name: str = events.get('OriginalRestApiGwStageName')
    original_resource_path: str = events.get('OriginalRestApiGwResourcePath', '*')
    original_http_method: str = events.get('OriginalRestApiGwHttpMethod', '*')

    # Need to have it here to overcame issue DIG-853 during rollback case
    if original_stage_name.startswith('{{') and original_gateway_id.startswith('{{'):
        original_stage_name = original_gateway_id = ''

    if original_resource_path.startswith('{{'):
        original_resource_path = '*'

    if original_http_method.startswith('{{'):
        original_http_method = '*'

    assert usage_plan_id == original_usage_plan_id, f'Provided RestApiGwUsagePlanId: {usage_plan_id} is not equal to ' \
                                                    f'original RestApiGwUsagePlanId: {original_usage_plan_id}'

    assert gateway_id == original_gateway_id, f'Provided RestApiGwId: {gateway_id} is not equal to ' \
                                              f'original RestApiGwId: {original_gateway_id}'

    assert stage_name == original_stage_name, f'Provided RestApiGwStageName: {stage_name} is not equal to ' \
                                              f'original RestApiGwStageName: {original_stage_name}'

    assert resource_path == original_resource_path, f'Provided RestApiGwResourcePath: {resource_path} is not equal to' \
                                                    f' original RestApiGwResourcePath: {original_resource_path}'

    assert http_method == original_http_method, f'Provided RestApiGwHttpMethod: {http_method} is not equal to ' \
                                                f'original RestApiGwHttpMethod: {original_http_method}'


def get_endpoint_security_group_config(events: dict, context: dict) -> dict:
    if 'RestApiGwId' not in events:
        raise KeyError('Requires RestApiGwId in events')

    gateway_id: str = events['RestApiGwId']
    provided_security_group_ids: list = events.get('SecurityGroupIdListToUnassign')

    apigw_client = boto3.client('apigateway')
    ec2_client = boto3.client('ec2')
    vpc_endpoint_ids: list = apigw_client.get_rest_api(restApiId=gateway_id)['endpointConfiguration']['vpcEndpointIds']

    if not vpc_endpoint_ids:
        raise Exception('Provided REST API gateway does not have any configured VPC endpoint')

    vpc_endpoint_configs: dict = ec2_client.describe_vpc_endpoints(VpcEndpointIds=vpc_endpoint_ids)['VpcEndpoints']
    vpc_endpoint_security_groups_map: dict = {}

    for vpc_endpoint in vpc_endpoint_configs:
        vpc_endpoint_security_groups_map[vpc_endpoint['VpcEndpointId']] = vpc_endpoint['Groups']

    if provided_security_group_ids:
        security_group_found = False
        for vpc_endpoint_id, security_groups_config in vpc_endpoint_security_groups_map.items():
            for security_group in security_groups_config:
                if security_group['GroupId'] not in provided_security_group_ids:
                    vpc_endpoint_security_groups_map[vpc_endpoint_id].remove(security_group)
                else:
                    security_group_found = True
        if not security_group_found:
            raise Exception('Provided security groups were not found in any configured VPC endpoint')

    return {"VpcEndpointsSecurityGroupsMappingOriginalValue": json.dumps(vpc_endpoint_security_groups_map)}


def update_endpoint_security_group_config(events: dict, context: dict) -> None:
    if 'VpcEndpointsSecurityGroupsMapping' not in events:
        raise KeyError('Requires VpcEndpointsSecurityGroupsMapping in events')

    vpc_endpoint_security_groups_map: dict = json.loads(events.get('VpcEndpointsSecurityGroupsMapping'))
    action: str = events.get('Action')

    if action not in ['ReplaceWithOriginalSg', 'ReplaceWithDummySg']:
        raise KeyError('Possible values for Action: ReplaceWithOriginalSg, ReplaceWithDummySg')

    ec2_client = boto3.client('ec2')

    for vpc_endpoint_id, security_groups_config in vpc_endpoint_security_groups_map.items():
        original_security_group_ids = [security_group['GroupId']
                                       for security_group in security_groups_config]

        dummy_sg_name = 'dummy-sg-' + vpc_endpoint_id
        describe_dummy_sg_args = {'Filters': [dict(Name='group-name', Values=[dummy_sg_name])]}
        describe_dummy_sg = ec2_client.describe_security_groups(**describe_dummy_sg_args)['SecurityGroups']
        dummy_sg_id = describe_dummy_sg[0]['GroupId'] if describe_dummy_sg else None

        if action == 'ReplaceWithDummySg':
            if not dummy_sg_id:
                log.debug(f'Creating dummy security group {dummy_sg_name} ...')
                vpc_id = ec2_client.describe_vpc_endpoints(VpcEndpointIds=[vpc_endpoint_id])['VpcEndpoints'][0]['VpcId']
                log.debug(f'VPC ID: {vpc_id}')
                create_dummy_sg_args = {
                    'VpcId': vpc_id,
                    'GroupName': dummy_sg_name,
                    'Description': 'Dummy SG',
                    'TagSpecifications': [
                        {
                            'ResourceType': 'security-group',
                            'Tags': [
                                {
                                    'Key': 'Digito',
                                    'Value': 'api-gw:test:simulate_network_unavailable'
                                }
                            ]
                        }
                    ]
                }
                dummy_sg_id = ec2_client.create_security_group(**create_dummy_sg_args)['GroupId']
                log.debug(f'Dummy security group {dummy_sg_name} successfully created ID: {dummy_sg_id}')
            else:
                log.debug(f'Dummy security group {dummy_sg_name} already exists with ID: {dummy_sg_id}')

            add_security_group_ids = [dummy_sg_id]
            remove_security_group_ids = original_security_group_ids

        elif action == 'ReplaceWithOriginalSg':
            add_security_group_ids = original_security_group_ids
            remove_security_group_ids = [dummy_sg_id] if dummy_sg_id else []

        log.debug(f'Modifying VPC endpoint {vpc_endpoint_id}')
        log.debug(f'AddSecurityGroupIds: {add_security_group_ids}')
        log.debug(f'RemoveSecurityGroupIds: {remove_security_group_ids}')
        response = ec2_client.modify_vpc_endpoint(VpcEndpointId=vpc_endpoint_id,
                                                  AddSecurityGroupIds=add_security_group_ids,
                                                  RemoveSecurityGroupIds=remove_security_group_ids)
        if not response['Return']:
            log.error(response)
            raise Exception('Could not modify VPC endpoint')
        else:
            log.debug(f'VPC endpoint {vpc_endpoint_id} modified successfully')

        if action == 'ReplaceWithOriginalSg' and dummy_sg_id:
            log.debug(f'Deleting dummy security group {dummy_sg_name} with ID {dummy_sg_id} ...')
            delete_sg_response = ec2_client.delete_security_group(GroupId=dummy_sg_id)
            log.debug(
                f'Delete security group response code: {delete_sg_response["ResponseMetadata"]["HTTPStatusCode"]}')
