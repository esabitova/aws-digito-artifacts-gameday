# coding=utf-8
"""SSM automation document for Aurora cluster failover. feature tests."""

from pytest_bdd import (
    scenario
)


@scenario('../features/asg_cpu_load.feature',
          'Create AWS resources using CloudFormation template and execute '
          'SSM automation CPU stress on ASG instances')
def test_cpu_stress_on_asg():
    """Create AWS resources using CloudFormation template and execute '
    'SSM automation CPU stress on ASG instances."""


@scenario('../../Tests/features/asg_cpu_load.feature',
          'Create AWS resources using CloudFormation template and execute '
          'SSM automation CPU stress on ASG instances with rollback')
def test_cpu_stress_on_asg_instance_with_rollback():
    """Create AWS resources using CloudFormation template and execute '
          'SSM automation CPU stress on ASG instances with rollback."""