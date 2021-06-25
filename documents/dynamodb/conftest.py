import json
import logging

import jsonpath_ng
import pytest
from pytest_bdd import given, parsers, when
from pytest_bdd.steps import then
from resource_manager.src.util import param_utils
from resource_manager.src.util.auto_scaling_utils import (
    _describe_scalable_targets_for_dynamodb_table,
    deregister_all_scaling_target_all_dynamodb_table)
from resource_manager.src.util.cloudwatch_utils import (
    delete_alarms_for_dynamo_db_table, get_metric_alarms_for_table)
from resource_manager.src.util.common_test_utils import (extract_param_value,
                                                         put_to_ssm_test_cache)
from resource_manager.src.util.dynamo_db_utils import (
    DynamoDbIndexType, get_secondary_indexes, _get_global_table_all_regions, add_global_table_and_wait_for_active,
    create_backup_and_wait_for_available, delete_backup_and_wait,
    get_item_async_stress_test, generate_random_item,
    drop_and_wait_dynamo_db_table_if_exists, get_continuous_backups_status,
    get_contributor_insights_status_for_table_and_indexes,
    get_earliest_recovery_point_in_time, get_kinesis_destinations, get_stream_settings, get_time_to_live,
    remove_global_table_and_wait_for_active, wait_table_to_be_active)


@pytest.fixture(scope='function')
def dynamodb_table_teardown(resource_pool, ssm_test_cache, boto3_session, target_table_name_ref,
                            global_table_secondary_region_ref):
    yield
    cf_output = resource_pool.get_cfn_output_params()
    param_containers = {'cfn-output': cf_output, 'cache': ssm_test_cache}
    table_name = param_utils.parse_param_value(
        target_table_name_ref, param_containers)
    region_global_table = param_utils.parse_param_value(
        global_table_secondary_region_ref, param_containers)
    wait_sec = 600
    delay_sec = 20

    remove_global_table_and_wait_for_active(table_name=table_name,
                                            global_table_regions=[region_global_table],
                                            wait_sec=wait_sec,
                                            delay_sec=delay_sec,
                                            boto3_session=boto3_session)

    deregister_all_scaling_target_all_dynamodb_table(boto3_session=boto3_session, table_name=table_name)

    delete_alarms_for_dynamo_db_table(boto3_session=boto3_session,
                                      table_name=table_name)

    drop_and_wait_dynamo_db_table_if_exists(table_name=table_name,
                                            boto3_session=boto3_session,
                                            wait_sec=wait_sec,
                                            delay_sec=delay_sec)


@pytest.fixture(scope='function')
def dynamodb_global_table_teardown(resource_pool, ssm_test_cache, boto3_session,
                                   table_name_ref,
                                   region_global_table_ref,
                                   wait_sec,
                                   delay_sec):
    """
    Meant to be used for source table.
    We only need to disable replication but the table itself will be deleted by rolling back CFN stack
    """
    yield
    cf_output = resource_pool.get_cfn_output_params()
    param_containers = {'cfn-output': cf_output, 'cache': ssm_test_cache}
    table_name = param_utils.parse_param_value(
        table_name_ref, param_containers)
    region_global_table = param_utils.parse_param_value(
        region_global_table_ref, param_containers)

    remove_global_table_and_wait_for_active(table_name=table_name,
                                            global_table_regions=[region_global_table],
                                            wait_sec=int(wait_sec),
                                            delay_sec=int(delay_sec),
                                            boto3_session=boto3_session)


@pytest.fixture(scope='function')
def dynamodb_delete_backup(ssm_test_cache, boto3_session,
                           wait_sec, delay_sec):
    """
    """
    yield
    containers = {'cache': ssm_test_cache}
    backup_arn = param_utils.parse_param_value("{{cache:BackupArn}}", containers)
    delete_backup_and_wait(backup_arn=backup_arn,
                           boto3_session=boto3_session,
                           wait_sec=int(wait_sec),
                           delay_sec=int(delay_sec))


@given(parsers.parse('register cleanup steps for table {target_table_name_ref} '
                     'with global table secondary region {global_table_secondary_region_ref}'))
def register_tear_down(resource_pool, ssm_test_cache, boto3_session, target_table_name_ref,
                       global_table_secondary_region_ref, dynamodb_table_teardown):
    logging.info('cleanup steps registered')


@given(parsers.parse('cache table property "{json_path}" as "{cache_property}" "{step_key}" SSM automation execution'
                     '\n{input_parameters}'))
@when(parsers.parse('cache table property "{json_path}" as "{cache_property}" "{step_key}" SSM automation execution'
                    '\n{input_parameters}'))
@then(parsers.parse('cache table property "{json_path}" as "{cache_property}" "{step_key}" SSM automation execution'
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
                                                     delay_sec,
                                                     dynamodb_delete_backup):
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
                        delay_sec,
                        dynamodb_global_table_teardown):
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


@then(parsers.parse('assert alarm {original_alarm_name_ref} copied for table {target_table_name_ref}'))
def assert_alarms_copied(resource_pool, ssm_test_cache, boto3_session,
                         target_table_name_ref,
                         original_alarm_name_ref):
    cf_output = resource_pool.get_cfn_output_params()
    containers = {'cfn-output': cf_output, 'cache': ssm_test_cache}
    table_name = param_utils.parse_param_value(target_table_name_ref, containers)
    alarm_name = param_utils.parse_param_value(original_alarm_name_ref, containers)
    alarms = list(get_metric_alarms_for_table(boto3_session=boto3_session,
                  table_name=table_name, alarms_names=[f"{alarm_name}_{table_name}"]))
    logging.info(f'target table: {table_name}, original_alarm_name: {alarm_name}, alarms queried: {alarms}')

    assert len(alarms) == 1


@given(parsers.parse('assert global table region {secondary_region_ref} copied for table {target_table_name_ref}'))
@then(parsers.parse('assert global table region {secondary_region_ref} copied for table {target_table_name_ref}'))
def assert_global_table_copied(resource_pool, ssm_test_cache, boto3_session,
                               target_table_name_ref,
                               secondary_region_ref):
    cf_output = resource_pool.get_cfn_output_params()
    containers = {'cfn-output': cf_output, 'cache': ssm_test_cache}
    table_name = param_utils.parse_param_value(target_table_name_ref, containers)
    region_name = param_utils.parse_param_value(secondary_region_ref, containers)
    replicas = _get_global_table_all_regions(boto3_session=boto3_session, table_name=table_name)
    logging.info(f'target table: {table_name}, region name: {region_name}, copied replicas: {replicas}')

    assert any(r['RegionName'] == region_name for r in replicas)


@given(parsers.parse('put random test item and cache it as "{item_ref}"\n{input_parameters}'))
@when(parsers.parse('put random test item and cache it as "{item_ref}"\n{input_parameters}'))
def put_item(boto3_session, resource_pool, ssm_test_cache, item_ref, input_parameters):
    dynamo_db_client = boto3_session.client('dynamodb')
    table_name: str = extract_param_value(input_parameters, "DynamoDBTableName", resource_pool, ssm_test_cache)
    item = generate_random_item(boto3_session, table_name)
    dynamo_db_client.put_item(TableName=table_name, Item=item)
    ssm_test_cache[item_ref] = item


@given(parsers.parse('get test item "{item_ref}" "{number}" times\n{input_parameters}'))
@when(parsers.parse('get test item "{item_ref}" "{number}" times\n{input_parameters}'))
def get_items(boto3_session, resource_pool, ssm_test_cache, item_ref, number, input_parameters):
    table_name: str = extract_param_value(input_parameters, "DynamoDBTableName", resource_pool, ssm_test_cache)
    item: dict = ssm_test_cache[item_ref]
    get_item_async_stress_test(boto3_session, table_name, int(number), item)


@then(parsers.parse('assert scaling targets copied from {source_table_name_ref} to {target_table_name_ref}'))
def assert_scaling_targets_copied(resource_pool, ssm_test_cache, boto3_session,
                                  target_table_name_ref,
                                  source_table_name_ref):
    cf_output = resource_pool.get_cfn_output_params()
    containers = {'cfn-output': cf_output, 'cache': ssm_test_cache}
    source_table_name = param_utils.parse_param_value(source_table_name_ref, containers)
    target_table_name = param_utils.parse_param_value(target_table_name_ref, containers)
    source_scalable_targets = _describe_scalable_targets_for_dynamodb_table(
        boto3_session=boto3_session, table_name=source_table_name)
    target_scalable_targets = _describe_scalable_targets_for_dynamodb_table(
        boto3_session=boto3_session, table_name=target_table_name)

    assert sorted(source_scalable_targets, key=lambda x: json.dumps(x, sort_keys=True)) ==\
        sorted(target_scalable_targets, key=lambda x: json.dumps(x, sort_keys=True))


@then(parsers.parse('assert indexes copied from {source_table_name_ref} to {target_table_name_ref}'))
def assert_indexes_copied(resource_pool, ssm_test_cache, boto3_session,
                          target_table_name_ref,
                          source_table_name_ref):
    cf_output = resource_pool.get_cfn_output_params()
    containers = {'cfn-output': cf_output, 'cache': ssm_test_cache}
    source_table_name = param_utils.parse_param_value(source_table_name_ref, containers)
    target_table_name = param_utils.parse_param_value(target_table_name_ref, containers)
    for index_type in list(DynamoDbIndexType):
        source_indexes = get_secondary_indexes(boto3_session=boto3_session,
                                               table_name=source_table_name,
                                               index_type=index_type)
        target_indexes = get_secondary_indexes(boto3_session=boto3_session,
                                               table_name=target_table_name,
                                               index_type=index_type)

        assert sorted(source_indexes, key=lambda x: json.dumps(x, sort_keys=True)) ==\
            sorted(target_indexes, key=lambda x: json.dumps(x, sort_keys=True))


@then(parsers.parse('assert contributor insights copied from {source_table_name_ref} to {target_table_name_ref}'))
def assert_contributor_insights_copied(resource_pool, ssm_test_cache, boto3_session,
                                       target_table_name_ref,
                                       source_table_name_ref):
    cf_output = resource_pool.get_cfn_output_params()
    containers = {'cfn-output': cf_output, 'cache': ssm_test_cache}
    source_table_name = param_utils.parse_param_value(source_table_name_ref, containers)
    target_table_name = param_utils.parse_param_value(target_table_name_ref, containers)

    source_table_contributor_insights, source_indexes_contributor_insights = \
        get_contributor_insights_status_for_table_and_indexes(boto3_session=boto3_session, table_name=source_table_name)

    target_table_contributor_insights, target_indexes_contributor_insights = \
        get_contributor_insights_status_for_table_and_indexes(boto3_session=boto3_session, table_name=target_table_name)

    assert source_table_contributor_insights == target_table_contributor_insights
    assert sorted(source_indexes_contributor_insights, key=lambda x: json.dumps(x, sort_keys=True)) ==\
        sorted(target_indexes_contributor_insights, key=lambda x: json.dumps(x, sort_keys=True))


@then(parsers.parse('assert stream copied from {source_table_name_ref} to {target_table_name_ref}'))
def assert_stream_settings_copied(resource_pool, ssm_test_cache, boto3_session,
                                  target_table_name_ref,
                                  source_table_name_ref):
    cf_output = resource_pool.get_cfn_output_params()
    containers = {'cfn-output': cf_output, 'cache': ssm_test_cache}
    source_table_name = param_utils.parse_param_value(source_table_name_ref, containers)
    target_table_name = param_utils.parse_param_value(target_table_name_ref, containers)

    source_stream_enabled, source_stream_type = \
        get_stream_settings(boto3_session=boto3_session, table_name=source_table_name)

    target_stream_enabled, target_stream_type = \
        get_stream_settings(boto3_session=boto3_session, table_name=target_table_name)

    assert source_stream_enabled == target_stream_enabled
    assert source_stream_type == target_stream_type


@then(parsers.parse('assert kinesis destinations copied from {source_table_name_ref} to {target_table_name_ref}'))
def assert_kinesis_destinations_copied(resource_pool, ssm_test_cache, boto3_session,
                                       target_table_name_ref,
                                       source_table_name_ref):
    cf_output = resource_pool.get_cfn_output_params()
    containers = {'cfn-output': cf_output, 'cache': ssm_test_cache}
    source_table_name = param_utils.parse_param_value(source_table_name_ref, containers)
    target_table_name = param_utils.parse_param_value(target_table_name_ref, containers)

    source_kinesis_destinations = \
        get_kinesis_destinations(boto3_session=boto3_session, table_name=source_table_name)

    target_kinesis_destinations = \
        get_kinesis_destinations(boto3_session=boto3_session, table_name=target_table_name)

    assert sorted(source_kinesis_destinations, key=lambda x: json.dumps(x, sort_keys=True)) ==\
        sorted(target_kinesis_destinations, key=lambda x: json.dumps(x, sort_keys=True))


@then(parsers.parse('assert time-to-live copied from {source_table_name_ref} to {target_table_name_ref}'))
def assert_ttl_copied(resource_pool, ssm_test_cache, boto3_session,
                      target_table_name_ref,
                      source_table_name_ref):
    cf_output = resource_pool.get_cfn_output_params()
    containers = {'cfn-output': cf_output, 'cache': ssm_test_cache}
    source_table_name = param_utils.parse_param_value(source_table_name_ref, containers)
    target_table_name = param_utils.parse_param_value(target_table_name_ref, containers)

    source_ttl = \
        get_time_to_live(boto3_session=boto3_session, table_name=source_table_name)

    target_ttl = \
        get_time_to_live(boto3_session=boto3_session, table_name=target_table_name)

    assert source_ttl == target_ttl


@then(parsers.parse('assert continuous backups settings copied from '
                    '{source_table_name_ref} to {target_table_name_ref}'))
def assert_continuous_backups_copied(resource_pool, ssm_test_cache, boto3_session,
                                     target_table_name_ref,
                                     source_table_name_ref):
    cf_output = resource_pool.get_cfn_output_params()
    containers = {'cfn-output': cf_output, 'cache': ssm_test_cache}
    source_table_name = param_utils.parse_param_value(source_table_name_ref, containers)
    target_table_name = param_utils.parse_param_value(target_table_name_ref, containers)

    source_continuous_backups_status = \
        get_continuous_backups_status(boto3_session=boto3_session, table_name=source_table_name)

    target_continuous_backups_status = \
        get_continuous_backups_status(boto3_session=boto3_session, table_name=target_table_name)

    assert source_continuous_backups_status == target_continuous_backups_status


@given(parsers.parse('cache different region name as "{cache_property}" "{step_key}" '
                     'SSM automation execution'))
@when(parsers.parse('cache different region name as "{cache_property}" "{step_key}" '
                    'SSM automation execution'))
def cache_different_region(boto3_session, ssm_test_cache,
                           cache_property, step_key):

    source_region = boto3_session.region_name
    available_region_list = boto3_session.get_available_regions('dynamodb')
    available_region_list.remove(source_region)
    logging.info(f'Available region list: {available_region_list}')
    # choose the first region from a location where step was run
    # if location contains only one region, choose the first one from other location
    destination_region = available_region_list[0]
    for region in available_region_list:
        if region.startswith(source_region.split('-')[0]):
            destination_region = region
            break
    logging.info(f'Caching new region for DynamoDB: {destination_region}')
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, destination_region)
