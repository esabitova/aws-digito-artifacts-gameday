# coding=utf-8
"""SSM automation document for ASG scale out feature tests."""

from pytest_bdd import (
    scenario
)


@scenario('../features/asg_scale_out.feature',
          'Create AWS resources using CloudFormation template and execute '
          'SSM automation scale out on ASG instances')
def test_asg_scale_out():
    """Create AWS resources using CloudFormation template and execute '
    'SSM automation scale out on ASG instances."""
