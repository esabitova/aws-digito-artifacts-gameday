from resource_manager.src.util.cloudwatch_utils import delete_alarms_for_dynamo_db_table
import jsonpath_ng
from pytest_bdd import given, parsers, then, when
from resource_manager.src.util import param_utils
from resource_manager.src.util.auto_scaling_utils import \
    deregister_all_scaling_target_all_dynamodb_table
from resource_manager.src.util.common_test_utils import (extract_param_value,
                                                         put_to_ssm_test_cache)
from resource_manager.src.util.dynamo_db_utils import (
    add_global_table_and_wait_for_active,
    create_backup_and_wait_for_available, delete_backup_and_wait,
    drop_and_wait_dynamo_db_table_if_exists,
    get_earliest_recovery_point_in_time,
    remove_global_table_and_wait_for_active, wait_table_to_be_active)


@given(parsers.parse('cache table property "{json_path}" as "{cache_property}" "{step_key}" SSM automation execution'
                     '\n{input_parameters}'))
@when(parsers.parse('cache table property "{json_path}" as "{cache_property}" "{step_key}" SSM automation execution'
                    '\n{input_parameters}'))
def cache_table_property(resource_pool, ssm_test_cache, boto3_session, json_path, cache_property, step_key,
                         input_parameters):
    dynamodb_client = boto3_session.client('dynamodb')
    table_name_value = extract_param_value(input_parameters, 'TableName', resource_pool, ssm_test_cache)
    response = dynamodb_client.describe_table(TableName=table_name_value)
    target_value = jsonpath_ng.parse(json_path).find(response)[0].value
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, target_value)


@given(parsers.parse("wait table {table_name_ref} to be active "
                     "for {wait_sec} seconds with interval {delay_sec} seconds"))
def wait_table_to_be_active_for_x_seconds(ssm_test_cache,
                                          resource_pool,
                                          boto3_session,
                                          table_name_ref,
                                          wait_sec,
                                          delay_sec):
    cf_output = resource_pool.get_cfn_output_params()
    table_name = param_utils.parse_param_value(table_name_ref, {'cfn-output': cf_output, 'cache': ssm_test_cache})
    wait_table_to_be_active(table_name=table_name,
                            boto3_session=boto3_session,
                            wait_sec=int(wait_sec),
                            delay_sec=int(delay_sec))


@given(parsers.parse("Create backup {backup_name_ref} for table {table_name_ref} and wait "
                     "for {wait_sec} seconds with interval {delay_sec} seconds"))
def create_backup_and_wait_when_it_becomes_available(ssm_test_cache,
                                                     resource_pool,
                                                     boto3_session,
                                                     backup_name_ref,
                                                     table_name_ref,
                                                     wait_sec,
                                                     delay_sec):
    cf_output = resource_pool.get_cfn_output_params()
    containers = {'cfn-output': cf_output, 'cache': ssm_test_cache}
    table_name = param_utils.parse_param_value(table_name_ref, containers)
    backup_name = param_utils.parse_param_value(backup_name_ref, containers)
    backup_arn = create_backup_and_wait_for_available(table_name=table_name,
                                                      backup_name=backup_name,
                                                      boto3_session=boto3_session,
                                                      wait_sec=int(wait_sec),
                                                      delay_sec=int(delay_sec))
    ssm_test_cache['BackupArn'] = backup_arn


@then(parsers.parse("Delete backup {backup_arn_ref} and wait "
                    "for {wait_sec} seconds with interval {delay_sec} seconds"))
def delete_backup_and_wait_it_gone(ssm_test_cache,
                                   resource_pool,
                                   boto3_session,
                                   backup_arn_ref,
                                   wait_sec,
                                   delay_sec):
    cf_output = resource_pool.get_cfn_output_params()
    containers = {'cfn-output': cf_output, 'cache': ssm_test_cache}
    backup_arn = param_utils.parse_param_value(backup_arn_ref, containers)
    delete_backup_and_wait(backup_arn=backup_arn,
                           boto3_session=boto3_session,
                           wait_sec=int(wait_sec),
                           delay_sec=int(delay_sec))


@given(parsers.parse("drop Dynamo DB table with the name {table_name_ref} and wait "
                     "for {wait_sec} seconds with interval {delay_sec} seconds"))
@then(parsers.parse("drop Dynamo DB table with the name {table_name_ref} and wait "
                    "for {wait_sec} seconds with interval {delay_sec} seconds"))
def drop_and_wait_dynamo_db_table(ssm_test_cache,
                                  resource_pool,
                                  boto3_session,
                                  table_name_ref,
                                  wait_sec,
                                  delay_sec):
    cf_output = resource_pool.get_cfn_output_params()
    table_name = param_utils.parse_param_value(table_name_ref, {'cfn-output': cf_output, 'cache': ssm_test_cache})
    drop_and_wait_dynamo_db_table_if_exists(table_name=table_name,
                                            boto3_session=boto3_session,
                                            wait_sec=int(wait_sec),
                                            delay_sec=int(delay_sec))


@given(parsers.parse("find a valid recovery point in time for {table_name_ref} and cache it as {field_name}"))
def find_valid_recovery_point_in_time(ssm_test_cache,
                                      resource_pool,
                                      boto3_session,
                                      table_name_ref,
                                      field_name):
    cf_output = resource_pool.get_cfn_output_params()
    table_name = param_utils.parse_param_value(table_name_ref, {'cfn-output': cf_output, 'cache': ssm_test_cache})
    valid_recovery_point = \
        get_earliest_recovery_point_in_time(table_name=table_name, boto3_session=boto3_session)

    ssm_test_cache[field_name] = str(valid_recovery_point.strftime("%Y-%m-%dT%H:%M:%S%z"))


@given(parsers.parse("enabled global dynamodb table {table_name_ref} in the region "
                     "{region_global_table_ref} and wait for "
                     "{wait_sec} seconds with delay {delay_sec} seconds"))
def enable_global_table(ssm_test_cache,
                        resource_pool,
                        boto3_session,
                        table_name_ref,
                        region_global_table_ref,
                        wait_sec,
                        delay_sec):
    cf_output = resource_pool.get_cfn_output_params()
    param_containers = {'cfn-output': cf_output, 'cache': ssm_test_cache}
    table_name = param_utils.parse_param_value(table_name_ref, param_containers)
    region_global_table = param_utils.parse_param_value(
        region_global_table_ref, param_containers)
    add_global_table_and_wait_for_active(table_name=table_name,
                                         global_table_regions=[region_global_table],
                                         wait_sec=int(wait_sec),
                                         delay_sec=int(delay_sec),
                                         boto3_session=boto3_session)


@then(parsers.parse("disable global dynamodb table {table_name_ref} in the region "
                    "{region_global_table_ref} and wait for "
                    "{wait_sec} seconds with delay {delay_sec} seconds"))
def disable_global_table(ssm_test_cache,
                         resource_pool,
                         boto3_session,
                         table_name_ref,
                         region_global_table_ref,
                         wait_sec,
                         delay_sec):
    cf_output = resource_pool.get_cfn_output_params()
    param_containers = {'cfn-output': cf_output, 'cache': ssm_test_cache}
    table_name = param_utils.parse_param_value(table_name_ref, param_containers)
    region_global_table = param_utils.parse_param_value(
        region_global_table_ref, param_containers)
    remove_global_table_and_wait_for_active(table_name=table_name,
                                            global_table_regions=[region_global_table],
                                            wait_sec=int(wait_sec),
                                            delay_sec=int(delay_sec),
                                            boto3_session=boto3_session)


@then(parsers.parse("deregister all scaling target for the table {table_name_cache_ref}"))
def deregister_all_scaling_targers_for_dynamodb_table(ssm_test_cache,
                                                      boto3_session,
                                                      table_name_cache_ref):
    table_name = param_utils.parse_param_value(table_name_cache_ref, {'cache': ssm_test_cache})
    deregister_all_scaling_target_all_dynamodb_table(boto3_session=boto3_session, table_name=table_name)


@then(parsers.parse("delete all alarms for the table {table_name_cache_ref}"))
def delete_all_alarms_for_dynamodb_table(ssm_test_cache,
                                         boto3_session,
                                         table_name_cache_ref):
    table_name = param_utils.parse_param_value(table_name_cache_ref,
                                               {'cache': ssm_test_cache})
    delete_alarms_for_dynamo_db_table(boto3_session=boto3_session,
                                      table_name=table_name)
