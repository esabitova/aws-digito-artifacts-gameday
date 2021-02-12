# coding=utf-8
"""SSM automation document for Aurora cluster failover. feature tests."""

from pytest_bdd import (
    scenario
)
from pytest import fixture
import logging

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