# coding=utf-8
"""SSM automation document for ASG memory injection. feature tests."""

from pytest_bdd import (
    scenario
)


@scenario('../features/asg_memory_load.feature',
          'Create AWS resources using CloudFormation template and execute '
          'SSM automation document ASG memory stress')
def test_memory_stress_on_asg():
    """Create AWS resources using CloudFormation template and execute '
    'SSM automation document ASG memory stress."""
