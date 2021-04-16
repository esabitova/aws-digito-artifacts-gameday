# coding=utf-8
"""SSM automation document to change REST API GW usage plan limits"""
from pytest_bdd import (
    scenario
)


@scenario('../features/change_quota_limit.feature',
          'Change REST API GW usage plan limits with ForceExecution=False')
def test_change_quota_limits_without_overwrite():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/change_quota_limit.feature',
          'Change REST API GW usage plan limits with ForceExecution=True')
def test_change_quota_limits_with_overwrite():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""
