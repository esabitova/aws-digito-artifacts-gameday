# coding=utf-8
"""Common utility functions for rds integration tests."""
import logging
from pytest_bdd import then, parsers, when, given
from sttable import parse_str_table

import resource_manager.src.util.param_utils as param_utils
import resource_manager.src.util.rds_util as rds_util
import pytz


@given(parsers.parse('cache DB cluster "{reader_cache_key}" and "{writer_cache_key}" as "{step_key}"\n'
                     '{input_parameters}'))
@when(parsers.parse('cache DB cluster "{reader_cache_key}" and "{writer_cache_key}" as "{step_key}"\n'
                    '{input_parameters}'))
@then(parsers.parse('cache DB cluster "{reader_cache_key}" and "{writer_cache_key}" as "{step_key}"\n'
                    '{input_parameters}'))
def cache_db_cluster_reader_writer(boto3_session, resource_pool, ssm_test_cache, reader_cache_key,
                                   writer_cache_key, step_key, input_parameters):
    param_val_ref = parse_str_table(input_parameters).rows[0]['ClusterId']
    cf_output = resource_pool.get_cfn_output_params()
    cluster_id = param_utils.parse_param_value(param_val_ref, {'cfn-output': cf_output, 'cache': ssm_test_cache})
    reader, writer = rds_util.get_reader_writer(cluster_id, boto3_session)
    ssm_test_cache[step_key] = {reader_cache_key: reader, writer_cache_key: writer}


@given(parsers.parse('assert db instance {db_instance} creation date is {operand} {start_time}'))
@then(parsers.parse('assert db instance {db_instance} creation date is {operand} {start_time}'))
def assert_db_instance_creation_date_after(resource_pool, ssm_test_cache, boto3_session,
                                           db_instance, start_time, operand):
    cf_output = resource_pool.get_cfn_output_params()
    containers = {'cfn-output': cf_output, 'cache': ssm_test_cache}
    db_instance_id = param_utils.parse_param_value(db_instance, containers)
    start_time_value = param_utils.parse_param_value(start_time, containers)

    instance = rds_util.get_db_instance_by_id(db_instance_id, boto3_session)
    logging.info(
        f'got instance details: {instance} for instance_id {db_instance_id}')

    if operand == 'after':
        assert instance['InstanceCreateTime'].replace(tzinfo=pytz.UTC) > start_time_value.replace(tzinfo=pytz.UTC)
    elif operand == 'before':
        assert instance['InstanceCreateTime'].replace(tzinfo=pytz.UTC) < start_time_value.replace(tzinfo=pytz.UTC)
    else:
        raise Exception(f'Operand with name {operand} is not supported. Supported operands: after | before.')
