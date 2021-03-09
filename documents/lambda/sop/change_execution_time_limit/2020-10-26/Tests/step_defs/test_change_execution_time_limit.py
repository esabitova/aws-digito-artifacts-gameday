# coding=utf-8
"""SSM automation document for changing Lambda execution time limit."""

from pytest_bdd import (
    scenario
)


@scenario('../features/change_execution_time_limit.feature',
          'Create AWS resources using CloudFormation template and execute SSM automation document for changing'
          ' execution time limit of Lambda')
def test_change_execution_time_limit():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""
