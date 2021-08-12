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
    result = trigger_lambda(lambda_arn=lambda_arn,
                            invocation_type=LambdaInvocationType.Event,
                            payload='{}',
                            session=boto3_session)
    logging.info(result['Payload'])
