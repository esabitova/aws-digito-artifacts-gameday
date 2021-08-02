import json
import logging
from pytest_bdd import given, parsers, when, then
from resource_manager.src.util.lambda_utils import trigger_lambda
from resource_manager.src.util.enums.lambda_invocation_type import LambdaInvocationType
from resource_manager.src.util.param_utils import parse_param_value
from sttable import parse_str_table

CIPHERS = (
    'AES128-GCM-SHA256:ECDHE-RSA-AES128-SHA256:AES256-SHA'
)


@given(parsers.parse('invoke lambda "{lambda_arn}" with parameters\n{input_parameters_table}'))
@when(parsers.parse('invoke lambda "{lambda_arn}" with parameters\n{input_parameters_table}'))
@then(parsers.parse('invoke lambda "{lambda_arn}" with parameters\n{input_parameters_table}'))
def invoke_lambda_function_with_parameters(
        boto3_session, resource_pool, cfn_output_params, ssm_test_cache, lambda_arn, input_parameters_table
):
    parameters = parse_str_table(input_parameters_table, False).rows

    lambda_arn = parse_param_value(lambda_arn, {'cache': ssm_test_cache, 'cfn-output': cfn_output_params})
    lambda_params = {}
    for item in parameters:
        param_name = item['0']
        param_value = parse_param_value(item['1'], {'cache': ssm_test_cache, 'cfn-output': cfn_output_params})
        lambda_params[param_name] = param_value

    payload = json.dumps(lambda_params)

    logging.info(f'Invoke lambda {lambda_arn} ...')
    result = trigger_lambda(lambda_arn=lambda_arn,
                            payload=payload,
                            invocation_type=LambdaInvocationType.Event,
                            session=boto3_session)
    logging.info(f'Lambda StatusCode: {result["StatusCode"]}')
    logging.info(f'Lambda Request ID: {result["ResponseMetadata"]["RequestId"]}')
