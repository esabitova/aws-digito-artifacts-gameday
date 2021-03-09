# coding=utf-8
"""SSM automation document for ec2 network unavailable feature tests."""

from pytest_bdd import (
    scenario
)


@scenario('../../Tests/features/ec2_network_unavailable.feature',
          'Create AWS resources using CloudFormation template and execute '
          'SSM automation network unavailable on EC2 instance')
def test_network_unavailable_on_ec2_instance():
    """Create AWS resources using CloudFormation template and execute '
    'SSM automation network unavailable on EC2 instance."""


@scenario('../../Tests/features/ec2_network_unavailable.feature',
          'Create AWS resources using CloudFormation template and execute '
          'SSM automation network unavailable on EC2 instance in rollback mode')
def test_network_unavailable_on_ec2_instance_in_rollback_mode():
    """Create AWS resources using CloudFormation template and execute '
    'SSM automation network unavailable on EC2 instance in rollback mode."""
