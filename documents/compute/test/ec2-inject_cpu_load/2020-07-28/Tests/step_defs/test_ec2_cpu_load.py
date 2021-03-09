# coding=utf-8
"""SSM automation document for Aurora cluster failover. feature tests."""

from pytest_bdd import (
    scenario
)


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
