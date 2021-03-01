# coding=utf-8
"""SSM automation document to restore an S3 bucket from a backup bucket"""

from pytest_bdd import (
    scenario,
    when,
    parsers,
    given
)

from resource_manager.src.util import s3_utils as s3_utils, iam_utils
from resource_manager.src.util.common_test_utils import put_to_ssm_test_cache, extract_param_value


@scenario('../features/restore_from_backup.feature',
          'Create AWS resources using CloudFormation template '
          'and execute SSM automation document to restore an S3 bucket from a backup bucket '
          'without approval to clean the restore bucket')
def test_restore_from_backup():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@given(parsers.parse('put "{number_of_files_to_put}" objects into the bucket'
                     '\n{input_parameters}'))
def put_objects(resource_manager, ssm_test_cache, number_of_files_to_put, input_parameters):
    s3_bucket_name = extract_param_value(input_parameters, "BucketName",
                                         resource_manager, ssm_test_cache)
    for i in range(int(number_of_files_to_put)):
        s3_utils.put_object(s3_bucket_name, f'{i}.txt', bytes(f'Content of the {i} file', encoding='utf-8'))


@given(parsers.parse('cache current user ARN as "{cache_property}" '
                     'at the bucket "{step_key}" SSM automation execution'))
def put_objects(resource_manager, ssm_test_cache, cache_property, step_key):
    user_arn = iam_utils.get_current_user_arn()
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, user_arn)


cache_value_expression = 'cache value of number of files as "{cache_property}" ' \
                         'at the bucket ' \
                         '"{step_key}" SSM automation execution' \
                         '\n{input_parameters}'


@given(parsers.parse(cache_value_expression))
@when(parsers.parse(cache_value_expression))
def cache_value_before_ssm(resource_manager, ssm_test_cache, cache_property, step_key,
                           input_parameters):
    populate_cache(resource_manager, ssm_test_cache, cache_property, step_key, "BucketName",
                   input_parameters)


def populate_cache(resource_manager, ssm_test_cache, cache_property, step_key, s3_bucket_name_property,
                   input_parameters):
    s3_bucket_name = extract_param_value(input_parameters, s3_bucket_name_property,
                                         resource_manager, ssm_test_cache)
    number_of_files = s3_utils.get_number_of_files(s3_bucket_name)
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, number_of_files)
