from resource_manager.src.util.dynamo_db_utils import drop_and_wait_dynamo_db_table_if_exists
from pytest_bdd import given, parsers, when, then
from resource_manager.src.util import lambda_utils, param_utils
from resource_manager.src.util.common_test_utils import (extract_param_value,
                                                         put_to_ssm_test_cache)

DROP_TABLE_DESCRIPTION = "Drop Dynamo DB table with the name {table_name_ref} and wait " \
    "for {wait_sec} seconds with interval {delay_sec} seconds"


@given(parsers.parse(DROP_TABLE_DESCRIPTION))
@then(parsers.parse(DROP_TABLE_DESCRIPTION))
def drop_and_wait_dynamo_db_table(ssm_test_cache,
                                  resource_manager,
                                  boto3_session,
                                  table_name_ref,
                                  wait_sec,
                                  delay_sec):
    cf_output = resource_manager.get_cfn_output_params()
    table_name = param_utils.parse_param_value(table_name_ref, {'cfn-output': cf_output, 'cache': ssm_test_cache})
    drop_and_wait_dynamo_db_table_if_exists(table_name=table_name,
                                            boto3_session=boto3_session,
                                            wait_sec=int(wait_sec),
                                            delay_sec=int(delay_sec))
