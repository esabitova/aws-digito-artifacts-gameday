# coding=utf-8
"""SSM automation document for Aurora cluster failover."""
from pytest_bdd import (
    scenario,
    then,
    when,
    parsers,
    given
)
import resource_manager.src.util.rds_util as rds_util
import resource_manager.src.util.param_utils as param_utils
from sttable import parse_str_table


@scenario('../../Tests/features/aurora_failover_cluster.feature','Create AWS resources using CloudFormation template and execute SSM automation document to failover RDS cluster with primary')
def test_failover_rds_cluster_automation_primary():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../../Tests/features/aurora_failover_cluster.feature','Create AWS resources using CloudFormation template and execute SSM automation document to failover RDS cluster default')
def test_failover_rds_cluster_automation_default():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@given(parsers.parse('cache DB cluster "{reader_cache_key}" and "{writer_cache_key}" "{step_key}" SSM automation execution\n{input_parameters}'))
def cache_db_cluster_instances_before_ssm(resource_manager, ssm_test_cache, reader_cache_key, writer_cache_key, step_key, input_parameters):
    populate_test_cache(resource_manager, ssm_test_cache, reader_cache_key, writer_cache_key, step_key, input_parameters)


@when(parsers.parse('cache DB cluster "{reader_cache_key}" and "{writer_cache_key}" "{step_key}" SSM automation execution\n{input_parameters}'))
def cache_db_cluster_instances_after_ssm(resource_manager, ssm_test_cache, reader_cache_key, writer_cache_key, step_key, input_parameters):
    populate_test_cache(resource_manager, ssm_test_cache, reader_cache_key, writer_cache_key, step_key, input_parameters)


@then(parsers.parse('assert DB cluster "{instance_role_key_one}" instance "{step_key_one}" failover became "{instance_role_key_two}" instance "{step_key_two}" failover'))
def assert_db_cluster(ssm_test_cache, instance_role_key_one, step_key_one, instance_role_key_two, step_key_two):
    assert ssm_test_cache[step_key_one][instance_role_key_one] == ssm_test_cache[step_key_two][instance_role_key_two]


def populate_test_cache(resource_manager, ssm_test_cache, reader_cache_key, writer_cache_key, step_key, input_parameters):
    param_val_ref = parse_str_table(input_parameters).rows[0]['ClusterId']
    cf_output = resource_manager.get_cf_output_params()
    cluster_id = param_utils.parse_param_value(param_val_ref, {'cfn-output': cf_output, 'cache': ssm_test_cache})
    reader, writer = rds_util.get_reader_writer(cluster_id)
    ssm_test_cache[step_key] = {reader_cache_key: reader, writer_cache_key: writer}





