from pytest_bdd import (
    given,
    parsers
)

from resource_manager.src.util import s3_utils as s3_utils
from resource_manager.src.util.common_test_utils import extract_param_value


@given(parsers.parse('clear the bucket'
                     '\n{input_parameters}'))
def clear_s3_bucket(resource_manager, ssm_test_cache, input_parameters):
    s3_bucket_name = extract_param_value(input_parameters, "BucketName",
                                         resource_manager, ssm_test_cache)
    s3_utils.clean_bucket(s3_bucket_name)
