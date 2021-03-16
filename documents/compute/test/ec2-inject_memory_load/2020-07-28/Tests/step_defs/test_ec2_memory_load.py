# coding=utf-8
"""SSM automation document for Aurora cluster failover. feature tests."""

from pytest_bdd import (
    scenario
)


@scenario('../features/ec2_memory_load.feature',
          'Create AWS resources using CloudFormation template and execute '
          'SSM automation memory stress on EC2 instance')
def test_memory_stress_on_ec2_instance():
    """Create AWS resources using CloudFormation template and execute '
    'SSM automation CPU stress on EC2 instance."""


@scenario('../features/ec2_memory_load.feature',
          'Create AWS resources using CloudFormation template and execute '
          'SSM automation memory stress on EC2 instance with rollback')
def test_memory_stress_on_ec2_instance_with_rollback():
    """Create AWS resources using CloudFormation template and execute '
          'SSM automation CPU stress on EC2 instance with rollback."""
