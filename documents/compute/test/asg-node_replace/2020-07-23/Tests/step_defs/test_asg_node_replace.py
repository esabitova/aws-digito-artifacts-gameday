# coding=utf-8
"""SSM automation document for ASG node replace feature tests."""

import pytest
from pytest_bdd import (
    scenario
)


@pytest.mark.skip(reason="Broken test: https://issues.amazon.com/issues/Digito-2905")
@scenario('../features/asg_node_replace.feature',
          'Create AWS resources using CloudFormation template and execute '
          'SSM automation node replace on ASG instances')
def test_node_replace_on_asg():
    """Create AWS resources using CloudFormation template and execute '
    'SSM automation node replace on ASG instances."""


@pytest.mark.skip(reason="Broken test: https://issues.amazon.com/issues/Digito-2904")
@scenario('../features/asg_node_replace.feature',
          'Create AWS resources using CloudFormation template and execute '
          'SSM automation node replace on ASG instances in rollback mode')
def test_node_replace_on_asg_rollback_mode():
    """Create AWS resources using CloudFormation template and execute '
    'SSM automation node replace on ASG instances in rollback mode."""
