# coding=utf-8
"""SSM automation document to Switch Alias of Lambda functions to another version"""
from pytest_bdd import (
    scenario
)


@scenario('../features/switch_lambda_version_in_alias.feature',
          'Switch Alias of Lambda functions to another version')
def test_switch_version():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""
