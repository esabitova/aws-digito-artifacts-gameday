# coding=utf-8
"""SSM automation document for Aurora cluster failover."""
from pytest_bdd import (
    scenario,
    then,
    parsers
)


@scenario('../../Tests/features/aurora_failover_cluster.feature', 'Create AWS resources using CloudFormation template '
                                                                  'and execute SSM automation document to failover '
                                                                  'RDS cluster with primary')
def test_failover_rds_cluster_automation_primary():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../../Tests/features/aurora_failover_cluster.feature', 'Create AWS resources using CloudFormation '
                                                                  'template and execute SSM automation document '
                                                                  'to failover RDS cluster default')
def test_failover_rds_cluster_automation_default():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@then(parsers.parse('assert DB cluster "{instance_role_key_one}" instance "{step_key_one}" failover became '
                    '"{instance_role_key_two}" instance "{step_key_two}" failover'))
def assert_db_cluster(ssm_test_cache, instance_role_key_one, step_key_one, instance_role_key_two, step_key_two):
    assert ssm_test_cache[step_key_one][instance_role_key_one] == ssm_test_cache[step_key_two][instance_role_key_two]
