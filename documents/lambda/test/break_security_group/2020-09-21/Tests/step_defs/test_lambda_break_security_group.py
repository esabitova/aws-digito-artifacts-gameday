from pytest_bdd import (
    scenario,
    given,
    parsers
)

from resource_manager.src.util.common_test_utils import put_to_ssm_test_cache


@scenario('../features/break_security_group_usual_case.feature',
          'Execute SSM automation document Digito-LambdaBreakSecurityGroup_2020-09-21')
def test_break_security_group_usual_case():
    """Execute SSM automation document Digito-LambdaBreakSecurityGroup_2020-09-21"""


# @scenario('../features/break_security_group_rollback_previous.feature',
#           'Execute SSM automation document Digito-LambdaBreakSecurityGroup_2020-09-21 in rollback')
# def test_break_security_group_rollback_previous():
#     """Execute SSM automation document Digito-LambdaBreakSecurityGroup_2020-09-21 in rollback"""
#
#
# @scenario('../features/break_security_group_failed.feature',
#           'Execute SSM automation document Digito-LambdaBreakSecurityGroup_2020-09-21 to test failure case')
# def test_break_security_group_failed():
#     """Execute SSM automation document Digito-LambdaBreakSecurityGroup_2020-09-21 to test failure case"""
#


@given(parsers.parse('cache lambda code for accessing s3 bucket as "{cache_property}" "{step_key}" '
                     'SSM automation execution'))
def cache_security_group(ssm_test_cache, cache_property, step_key, ):
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
