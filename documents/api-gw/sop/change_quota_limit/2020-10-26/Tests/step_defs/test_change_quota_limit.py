# coding=utf-8
"""SSM automation document to change REST API GW usage plan limits"""
from pytest_bdd import (
    scenario
)


@scenario('../features/change_quota_limit.feature',
          'Execute Digito-RestApiGwChangeQuotaLimit_2020-10-26 to change quota limit with new quota less than 50%')
def test_change_quota_limit_with_new_quota_less_than_50_percent():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/change_quota_limit.feature',
          'Execute Digito-RestApiGwChangeQuotaLimit_2020-10-26 to change quota limit with new quota more than 50%')
def test_change_quota_limit_with_new_quota_more_than_50_percent():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/change_quota_limit.feature',
          'Execute Digito-RestApiGwChangeQuotaLimit_2020-10-26 to change quota limit with ForceExecution=True')
def test_change_quota_limit_with_force_execution_true():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""
