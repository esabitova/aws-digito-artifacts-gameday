import json
import logging

import boto3
from pytest_bdd.parsers import parse
from pytest_bdd.steps import given, when

from resource_manager.src.util.enums.lambda_invocation_type import \
    LambdaInvocationType
from resource_manager.src.util.lambda_utils import trigger_lambda
from resource_manager.src.util.param_utils import parse_param_value


@given(parse('trigger lambda "{lambda_arn_ref}" asynchronously'))
@when(parse('trigger lambda "{lambda_arn_ref}" asynchronously'))
def trigger_lambda_async(resource_pool,
                         boto3_session: boto3.Session,
                         lambda_arn_ref: str):
    cf_output = resource_pool.get_cfn_output_params()
    lambda_arn = parse_param_value(lambda_arn_ref, {'cfn-output': cf_output})
    payload = json.dumps({
        'duration_sec': 720  # 12 minutes
    })
    result = trigger_lambda(lambda_arn=lambda_arn,
                            payload=payload,
                            invocation_type=LambdaInvocationType.Event,
                            session=boto3_session)
    logging.info(f"Lambda Function: {lambda_arn} has been triggered with the result {result['Payload']}")
