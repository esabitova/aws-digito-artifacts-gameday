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
