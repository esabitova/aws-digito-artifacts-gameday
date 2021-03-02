# coding=utf-8
"""SSM automation document to restore an S3 object into previous version"""
from typing import List

from pytest_bdd import (
    scenario,
    when,
    parsers,
    given
)

from resource_manager.src.util import s3_utils as s3_utils
from resource_manager.src.util.common_test_utils import put_to_ssm_test_cache, extract_param_value


@scenario('../features/restore_to_previous_version.feature',
          'Create AWS resources using CloudFormation template and execute SSM automation document '
          'to restore an S3 object into previous version')
def test_restore_previous_versions():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


cache_value_statement = 'cache value of "{version_indicator}" version of the "{file_name}" file as "{cache_property}" ' \
                        'at "{s3_bucket_param_key}" bucket "{step_key}" SSM automation execution' \
                        '\n{input_parameters}'


@when(parsers.parse(cache_value_statement))
@given(parsers.parse(cache_value_statement))
def cache_value_of_version(resource_manager, ssm_test_cache, version_indicator, file_name,
                           cache_property, s3_bucket_param_key, step_key,
                           input_parameters):
    populate_cache_value_of_version(cache_property, file_name, input_parameters, resource_manager, s3_bucket_param_key,
                                    ssm_test_cache, step_key, version_indicator)


def populate_cache_value_of_version(cache_property, file_name, input_parameters, resource_manager, s3_bucket_param_key,
                                    ssm_test_cache, step_key, version_indicator):
    s3_bucket_name: str = extract_param_value(input_parameters, s3_bucket_param_key,
                                              resource_manager, ssm_test_cache)
    versions: List = s3_utils.get_versions(s3_bucket_name, object_key=file_name, max_keys=2)
    if version_indicator == 'previous':
        if len(versions) < 2:
            raise KeyError(f'Can not get previous version because the number of versions is {len(versions)}')
        version_to_cache = versions[1]['VersionId']
    elif version_indicator == 'latest':
        version_to_cache = versions[0]['VersionId']
    else:
        raise KeyError(f'The version {version_indicator} is not processable')
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, version_to_cache)
