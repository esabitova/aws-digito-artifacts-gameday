# coding=utf-8
"""SSM automation document for ASG AZ Outage feature tests."""

from pytest_bdd import (
    scenario
)


@scenario('../features/asg_az_outage.feature',
          'Create AWS resources using CloudFormation template and execute '
          'SSM automation AZ outage on ASG instances')
def test_az_outage_on_asg():
    """Create AWS resources using CloudFormation template and execute '
    'SSM automation AZ outage on ASG instances."""


@scenario('../features/asg_az_outage.feature',
          'Create AWS resources using CloudFormation template and execute '
          'SSM automation AZ outage on ASG instances in rollback mode')
def test_az_outage_on_asg_rollback_mode():
    """Create AWS resources using CloudFormation template and execute '
    'SSM automation AZ outage on ASG instances in rollback mode."""
