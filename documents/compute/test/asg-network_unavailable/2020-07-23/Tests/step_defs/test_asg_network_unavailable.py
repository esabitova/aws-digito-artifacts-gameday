# coding=utf-8
"""SSM automation document for asg network unavailable feature tests."""

from pytest_bdd import (
    scenario
)


@scenario('../../Tests/features/asg_network_unavailable.feature',
          'Create AWS resources using CloudFormation template and execute '
          'SSM automation network unavailable on EC2 instances in ASG')
def test_network_unavailable_on_asg():
    """Create AWS resources using CloudFormation template and execute '
    'SSM automation network unavailable on EC2 instances in ASG."""
