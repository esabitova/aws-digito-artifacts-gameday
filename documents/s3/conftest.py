import logging

from boto3 import Session
from pytest_bdd import (
    given,
    parsers, when
)

from resource_manager.src.util import s3_utils as s3_utils
from resource_manager.src.util.common_test_utils import extract_param_value, put_to_ssm_test_cache


@given(parsers.parse('clear the bucket\n{input_parameters}'))
def clear_s3_bucket(resource_manager, ssm_test_cache, input_parameters, boto3_session):
    s3_bucket_name: str = extract_param_value(input_parameters, "BucketName", resource_manager, ssm_test_cache)
    s3_utils.clean_bucket(boto3_session, s3_bucket_name)


@given(parsers.parse('put "{object_key_to_put}" object "{times_to_put}" times with different content '
                     'into "{s3_bucket_name_property}" bucket'
                     '\n{input_parameters}'))
def put_different_objects_to_bucket(
        resource_manager, ssm_test_cache, object_key_to_put, times_to_put, s3_bucket_name_property, input_parameters
):
    s3_bucket_name: str = extract_param_value(
        input_parameters, s3_bucket_name_property, resource_manager, ssm_test_cache
    )
    for i in range(int(times_to_put)):
        content: str = f'Content of the file {object_key_to_put} written at {i} attempt'
        s3_utils.put_object(s3_bucket_name, object_key_to_put, bytes(content, encoding='utf-8'))


@when(parsers.parse('cache value of "{s3_property_name}" property of the "{object_key}" file '
                    'with the specific "{version_id_param_key}" version as "{cache_property}" '
                    'at "{s3_bucket_param_key}" bucket "{step_key}" SSM automation execution'
                    '\n{input_parameters}'))
@given(parsers.parse('cache value of "{s3_property_name}" property of the "{object_key}" file '
                     'with the specific "{version_id_param_key}" version as "{cache_property}" '
                     'at "{s3_bucket_param_key}" bucket "{step_key}" SSM automation execution'
                     '\n{input_parameters}'))
def cache_property_of_version(
        resource_manager, ssm_test_cache, s3_property_name, object_key, version_id_param_key,
        cache_property, s3_bucket_param_key, step_key, input_parameters
):
    populate_cache_property_of_version(
        resource_manager, ssm_test_cache, s3_property_name, object_key, version_id_param_key,
        cache_property, s3_bucket_param_key, step_key, input_parameters
    )


@when(parsers.parse('get the "{object_key}" object from bucket "{tries_number}" times with error\n{input_parameters}'))
@given(parsers.parse('get the "{object_key}" object from bucket "{tries_number}" times with error\n{input_parameters}'))
def get_object_with_error(resource_manager, ssm_test_cache, boto3_session: Session, object_key, tries_number,
                          input_parameters):
    s3_bucket_name = extract_param_value(input_parameters, "BucketName", resource_manager, ssm_test_cache)
    for i in range(int(tries_number)):
        try:
            boto3_session.client("s3").get_object(Bucket=s3_bucket_name, Key=object_key)
        except Exception as e:
            logging.info(f'Expected error occurred while calling '
                         f'get_object(Bucket={s3_bucket_name}, Key={object_key}): {e}')


@when(parsers.parse('get the "{object_key}" object from bucket "{tries_number}" times\n{input_parameters}'))
@given(parsers.parse('get the "{object_key}" object from bucket "{tries_number}" times\n{input_parameters}'))
def get_object(resource_manager, ssm_test_cache, boto3_session: Session, object_key, tries_number, input_parameters):
    s3_bucket_name = extract_param_value(input_parameters, "BucketName", resource_manager, ssm_test_cache)
    for i in range(int(tries_number)):
        boto3_session.client("s3").get_object(Bucket=s3_bucket_name, Key=object_key)


def populate_cache_property_of_version(
        resource_manager, ssm_test_cache, s3_property_name, object_key, version_id_param_key, cache_property,
        s3_bucket_param_key, step_key, input_parameters
):
    s3_bucket_name: str = extract_param_value(
        input_parameters, s3_bucket_param_key, resource_manager, ssm_test_cache
    )
    version_id: str = extract_param_value(
        input_parameters, version_id_param_key, resource_manager, ssm_test_cache
    )
    s3_property_value: dict = s3_utils.get_object(s3_bucket_name, object_key, version_id)[s3_property_name]

    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, s3_property_value)


@given(parsers.parse('put "{number_of_files_to_put}" objects into the bucket\n{input_parameters}'))
def put_objects_to_bucket(resource_manager, ssm_test_cache, number_of_files_to_put, input_parameters):
    s3_bucket_name = extract_param_value(
        input_parameters, "BucketName", resource_manager, ssm_test_cache
    )
    for i in range(int(number_of_files_to_put)):
        s3_utils.put_object(s3_bucket_name, f'{i}.txt', bytes(f'Content of the {i} file', encoding='utf-8'))


cache_number_of_files_value_expression = 'cache value of number of files as "{cache_property}" ' \
                                         'at the bucket "{step_key}" SSM automation execution' \
                                         '\n{input_parameters}'


@given(parsers.parse(cache_number_of_files_value_expression))
@when(parsers.parse(cache_number_of_files_value_expression))
def cache_value_before_ssm(
        resource_manager, ssm_test_cache, cache_property, step_key, input_parameters
):
    populate_cache_of_number_of_files(
        resource_manager, ssm_test_cache, cache_property, step_key, "BucketName", input_parameters
    )


def populate_cache_of_number_of_files(
        resource_manager, ssm_test_cache, cache_property, step_key, s3_bucket_name_property, input_parameters
):
    s3_bucket_name = extract_param_value(
        input_parameters, s3_bucket_name_property, resource_manager, ssm_test_cache
    )
    number_of_files = s3_utils.get_number_of_files(s3_bucket_name)
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, number_of_files)
