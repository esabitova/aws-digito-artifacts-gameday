from pytest_bdd import (
    scenario,
    given,
    when,
    then,
    parsers
)

import logging

from resource_manager.src.util.common_test_utils import put_to_ssm_test_cache, extract_param_value

logger = logging.getLogger()

cache_lambda_security_group_text = 'cache security group list for a lambda as "{cache_property}" "{step_key}" ' \
                                   'SSM automation execution\n{input_parameters}'


@scenario('../features/break_security_group_usual_case.feature',
          'Execute SSM automation document Digito-BreakLambdaSecurityGroupTest_2020-09-21')
def test_break_security_group_usual_case():
    """Execute SSM automation document Digito-BreakLambdaSecurityGroupTest_2020-09-21"""


@scenario('../features/break_security_group_usual_case_specify_sg.feature',
          'Execute SSM automation document Digito-BreakLambdaSecurityGroupTest_2020-09-21')
def test_break_security_group_usual_case_specify_sg():
    """Execute SSM automation document Digito-BreakLambdaSecurityGroupTest_2020-09-21"""


@scenario('../features/break_security_group_rollback_previous.feature',
          'Execute SSM automation document Digito-BreakLambdaSecurityGroupTest_2020-09-21 in rollback')
def test_break_security_group_rollback_previous():
    """Execute SSM automation document Digito-BreakLambdaSecurityGroupTest_2020-09-21 in rollback"""


@scenario('../features/break_security_group_failed.feature',
          'Execute SSM automation document Digito-BreakLambdaSecurityGroupTest_2020-09-21 to test failure case')
def test_break_security_group_failed():
    """Execute SSM automation document Digito-BreakLambdaSecurityGroupTest_2020-09-21 to test failure case"""


@given(parsers.parse('cache lambda code for accessing s3 bucket as "{cache_property}" "{step_key}" '
                     'SSM automation execution'))
def cache_lambda_code(ssm_test_cache, cache_property, step_key):
    lambda_code = """
import boto3
import time

def handler(event, context):

    s3 = boto3.resource(
        's3'
    )
    my_bucket = s3.Bucket(event['bucket_name'])
    for my_bucket_object in my_bucket.objects.all():
        print(my_bucket_object)
    """
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, lambda_code)


@given(parsers.parse(cache_lambda_security_group_text))
@when(parsers.parse(cache_lambda_security_group_text))
@then(parsers.parse(cache_lambda_security_group_text))
def cache_lambda_security_group_list(resource_pool, boto3_session,
                                     ssm_test_cache, input_parameters, cache_property, step_key):
    lambda_arn = extract_param_value(input_parameters, 'LambdaARN', resource_pool, ssm_test_cache)
    lambda_client = boto3_session.client('lambda')
    lambda_description = lambda_client.get_function(
        FunctionName=lambda_arn
    )
    if 'VpcId' in lambda_description['Configuration']['VpcConfig']:
        sg_list = lambda_description['Configuration']['VpcConfig']['SecurityGroupIds']
    else:
        raise AssertionError(f'Lambda function:{lambda_arn} is not a member of any VPC')

    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, sg_list)
