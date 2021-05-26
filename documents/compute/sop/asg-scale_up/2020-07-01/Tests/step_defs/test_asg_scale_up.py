# coding=utf-8
"""SSM automation document for ASG scale up feature tests."""

from pytest_bdd import (
    scenario
)


@scenario('../features/asg_scale_up.feature',
          'Create AWS resources using CloudFormation template and execute '
          'SSM automation scale up on ASG with LaunchConfig')
def test_asg_scale_up_launch_config():
    """Create AWS resources using CloudFormation template and execute '
    'SSM automation scale up on ASG with LaunchConfig."""


@scenario('../features/asg_scale_up.feature',
          'Create AWS resources using CloudFormation template and execute '
          'SSM automation scale up on ASG with LaunchTemplate')
def test_asg_scale_up_launch_template():
    """Create AWS resources using CloudFormation template and execute '
    'SSM automation scale up on ASG with LaunchTemplate."""
