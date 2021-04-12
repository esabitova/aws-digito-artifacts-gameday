from pytest_bdd import given, parsers, then
from resource_manager.src.util import param_utils
from resource_manager.src.util.dynamo_db_utils import \
    add_kinesis_destinations, \
    drop_and_wait_dynamo_db_table_if_exists, \
    get_earliest_recovery_point_in_time, \
    update_time_to_live

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


@given(parsers.parse("valid recovery point in time for {table_name_ref} and cache it as {field_name}"))
def find_valid_recovery_point_in_time(ssm_test_cache,
                                      resource_manager,
                                      boto3_session,
                                      table_name_ref,
                                      field_name):
    cf_output = resource_manager.get_cfn_output_params()
    table_name = param_utils.parse_param_value(table_name_ref, {'cfn-output': cf_output, 'cache': ssm_test_cache})
    valid_recovery_point = \
        get_earliest_recovery_point_in_time(table_name=table_name, boto3_session=boto3_session)

    ssm_test_cache[field_name] = str(valid_recovery_point.strftime("%Y-%m-%dT%H:%M:%S%z"))


@given(parsers.parse("enabled kinesis stream {kds_arn_ref} on dynamodb table {table_name_ref}"))
def enable_kinesis_streaming_destination(ssm_test_cache,
                                         resource_manager,
                                         boto3_session,
                                         table_name_ref,
                                         kds_arn_ref):
    cf_output = resource_manager.get_cfn_output_params()
    table_name = param_utils.parse_param_value(table_name_ref, {'cfn-output': cf_output, 'cache': ssm_test_cache})
    kds_arn = param_utils.parse_param_value(kds_arn_ref, {'cfn-output': cf_output, 'cache': ssm_test_cache})
    add_kinesis_destinations(table_name=table_name, kds_arn=kds_arn, boto3_session=boto3_session)


@given(parsers.parse("enabled ttl on dynamodb table {table_name_ref} with attribute name {attribute_name_ref}"))
def enable_tll(ssm_test_cache,
               resource_manager,
               boto3_session,
               table_name_ref,
               attribute_name_ref):
    cf_output = resource_manager.get_cfn_output_params()
    table_name = param_utils.parse_param_value(table_name_ref, {'cfn-output': cf_output, 'cache': ssm_test_cache})
    attribute_name = param_utils.parse_param_value(
        attribute_name_ref, {'cfn-output': cf_output, 'cache': ssm_test_cache})
    update_time_to_live(table_name=table_name,
                        is_enabled=True,
                        attribute_name=attribute_name,
                        boto3_session=boto3_session)
