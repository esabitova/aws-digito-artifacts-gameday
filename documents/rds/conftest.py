# coding=utf-8
"""Common utility functions for rds integration tests."""
from pytest_bdd import then, parsers, when, given
import resource_manager.src.util.rds_util as rds_util
import resource_manager.src.util.param_utils as param_utils
from sttable import parse_str_table


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
