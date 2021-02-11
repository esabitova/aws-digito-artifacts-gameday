# coding=utf-8
"""SSM automation document for Aurora cluster failover. feature tests."""

from pytest_bdd import (
    scenario,
    then,
    parsers,
    given,
    when
)
from pytest import fixture
from sttable import parse_str_table
from resource_manager.src.util.param_utils import parse_param_values_from_table
from resource_manager.src.util.cw_util import get_ec2_metric_max_datapoint
from resource_manager.src.util.ssm_utils import get_ssm_step_interval, get_ssm_step_status
import time
import logging
from datetime import datetime, timedelta


@scenario('../../Tests/features/ec2_cpu_load.feature',
          'Create AWS resources using CloudFormation template and execute '
          'SSM automation CPU stress on EC2 instance')
def test_cpu_stress_on_ec2_instance():
    """Create AWS resources using CloudFormation template and execute '
    'SSM automation CPU stress on EC2 instance."""


@scenario('../../Tests/features/ec2_cpu_load.feature',
          'Create AWS resources using CloudFormation template and execute '
          'SSM automation CPU stress on EC2 instance with rollback')
def test_cpu_stress_on_ec2_instance_with_rollback():
    """Create AWS resources using CloudFormation template and execute '
          'SSM automation CPU stress on EC2 instance with rollback."""


@when(parsers.parse('assert "{metric_name}" metric reached "{exp_perc}" percent(s)\n{input_params}'))
@then(parsers.parse('assert "{metric_name}" metric reached "{exp_perc}" percent(s)\n{input_params}'))
def assert_utilization(exp_perc, resource_manager, input_params, ssm_test_cache, boto3_session, metric_name):
    cf_output = resource_manager.get_cfn_output_params()
    params = parse_param_values_from_table(input_params, {'cfn-output': cf_output, 'cache': ssm_test_cache})
    instance_id = params[0]['InstanceId']
    exec_id = params[0]['ExecutionId']

    exec_start, exec_end = get_ssm_step_interval(boto3_session, exec_id, 'RunCpuStress')
    # Reported command execution start time given in SSM is delayed, so we need exclude that delay to find metric
    exec_start = exec_start - timedelta(seconds=300)
    act_perc = get_ec2_metric_max_datapoint(boto3_session, instance_id, metric_name, exec_start, datetime.utcnow())
    assert int(act_perc) >= int(exp_perc)


@then(parsers.parse('assert "{metric_name}" metric below "{exp_perc}" percent(s) after rollback\n{input_params}'))
def assert_utilization_after_rollback(boto3_session, resource_manager, input_params, ssm_test_cache, exp_perc, metric_name):
    cf_output = resource_manager.get_cfn_output_params()
    params = parse_param_values_from_table(input_params, {'cfn-output': cf_output, 'cache': ssm_test_cache})
    instance_id = params[0]['InstanceId']
    rollback_exec_id = params[0]['RollbackExecutionId']

    rollback_exec_start, rollback_exec_end = get_ssm_step_interval(boto3_session, rollback_exec_id, 'KillStressCommandOnRollback')
    # Reported command execution start time given in SSM is delayed, so we need exclude that delay to find metric
    rollback_exec_start = rollback_exec_start - timedelta(seconds=300)
    act_perc = get_ec2_metric_max_datapoint(boto3_session, instance_id, metric_name, rollback_exec_start, datetime.utcnow())
    assert int(act_perc) < int(exp_perc)


@fixture(autouse=True, scope='function')
def setup(request, ssm_test_cache, boto3_session):

    def tear_down():
        # Terminating SSM automation execution at the end of execution.
        ssm = boto3_session.client('ssm')
        cached_executions = ssm_test_cache.get('SsmExecutionId')
        if cached_executions is not None:
            for index, exec_id in cached_executions.items():
                logging.info("Canceling SSM execution with id [{}]".format(exec_id))
                ssm.stop_automation_execution(AutomationExecutionId=exec_id, Type='Cancel')

    request.addfinalizer(tear_down)
