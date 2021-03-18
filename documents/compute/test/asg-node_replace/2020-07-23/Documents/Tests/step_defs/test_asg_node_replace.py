# coding=utf-8
"""SSM automation document for ASG node replace feature tests."""

from pytest_bdd import (
    scenario
)


@scenario('../features/asg_node_replace.feature',
          'Create AWS resources using CloudFormation template and execute '
          'SSM automation node replace on ASG instances')
def test_node_replace_on_asg():
    """Create AWS resources using CloudFormation template and execute '
    'SSM automation node replace on ASG instances."""


@scenario('../features/asg_node_replace.feature',
          'Create AWS resources using CloudFormation template and execute '
          'SSM automation node replace on ASG instances in rollback mode')
def test_node_replace_on_asg_rollback_mode():
    """Create AWS resources using CloudFormation template and execute '
    'SSM automation node replace on ASG instances in rollback mode."""
