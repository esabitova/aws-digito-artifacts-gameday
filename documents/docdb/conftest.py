from pytest_bdd import (
    given,
    parsers
)

from documents.util.scripts.src import docdb_util as docdb_util
from resource_manager.src.util.common_test_utils import extract_param_value


@given(parsers.parse('put "{file_name_to_put}" object "{times_to_put}" times with different content '
                     'into "{s3_bucket_name_property}" bucket'
                     '\n{input_parameters}'))
def put_objects(resource_manager, ssm_test_cache, file_name_to_put, times_to_put,
                s3_bucket_name_property, input_parameters):
    s3_bucket_name = extract_param_value(input_parameters, s3_bucket_name_property,
                                         resource_manager, ssm_test_cache)
    for i in range(int(times_to_put)):
        s3_utils.put_object(s3_bucket_name, file_name_to_put,
                            bytes(f'Content of the file {file_name_to_put} written at {i} attempt', encoding='utf-8'))
