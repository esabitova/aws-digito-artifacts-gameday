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


@given(parsers.parse('the cached input parameters\n{input_parameters}'))
def given_cached_input_parameters(ssm_test_cache, input_parameters):
    for parm_name, param_val in parse_str_table(input_parameters).rows[0].items():
        ssm_test_cache[parm_name] = str(param_val)


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


@then(parsers.parse('sleep for "{seconds}" seconds'))
def sleep_secons(seconds):
    # Need to wait for more than 5 minutes for metric to be reported
    logging.info('Sleeping for [{}] seconds'.format(seconds))
    time.sleep(int(seconds))


@then(parsers.parse('assert SSM automation document step "{step_name}" execution in status "{expected_step_status}"\n{parameters}'))
def verify_step_in_status(boto3_session, step_name, expected_step_status, ssm_test_cache, parameters):
    params = parse_param_values_from_table(parameters, {'cache': ssm_test_cache})
    current_step_status = get_ssm_step_status(boto3_session, params[0]['ExecutionId'], step_name)
    assert expected_step_status == current_step_status


@when(parsers.parse('SSM automation document "{ssm_document_name}" executed with rollback\n{ssm_input_parameters}'))
def execute_ssm_with_rollback(ssm_document_name, ssm_input_parameters, ssm_test_cache, resource_manager, ssm_document):
    cfn_output = resource_manager.get_cfn_output_params()
    parameters = ssm_document.parse_input_parameters(cfn_output, ssm_test_cache, ssm_input_parameters)
    execution_id = ssm_document.execute(ssm_document_name, parameters)
    ssm_test_cache['SsmRollbackExecutionId'] = execution_id
    return execution_id


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


@then(parsers.parse('terminate "{ssm_document_name}" SSM automation document\n{input_parameters}'))
def terminate_ssm_execution(boto3_session, resource_manager, ssm_test_cache, ssm_document, input_parameters):
    ssm = boto3_session.client('ssm')
    cfn_output = resource_manager.get_cfn_output_params()
    parameters = ssm_document.parse_input_parameters(cfn_output, ssm_test_cache, input_parameters)
    ssm.stop_automation_execution(AutomationExecutionId=parameters['ExecutionId'][0], Type='Cancel')


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
