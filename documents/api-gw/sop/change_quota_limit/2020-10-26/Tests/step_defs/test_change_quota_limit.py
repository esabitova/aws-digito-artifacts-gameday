# coding=utf-8
"""SSM automation document to change REST API GW usage plan limits"""
from pytest_bdd import (
    scenario
)


@scenario('../features/change_quota_limit.feature',
          'Change REST API GW usage plan limits with ForceExecution=False and new quota is not more than 50%')
def test_change_quota_limits_without_overwrite_and_new_quota_is_no_more_than_50():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/change_quota_limit.feature',
          'Change REST API GW usage plan limits with ForceExecution=False and new quota is more than 50%')
def test_change_quota_limits_without_overwrite_and_new_quota_is_more_than_50():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/change_quota_limit.feature',
          'Change REST API GW usage plan limits with ForceExecution=True')
def test_change_quota_limits_with_overwrite():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""
