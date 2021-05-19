# coding=utf-8
"""SSM automation document to change REST API GW usage plan limits"""
from pytest_bdd import (
    scenario
)


@scenario('../features/change_throttling_settings_rest_normal_cases_without_overwrite.feature',
          'Change throttling settings for REST API Gateway with ForceExecution=False and '
          'without provided stage name')
def test_change_throttling_settings_rest_without_overwrite_and_without_provided_stage_name():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/change_throttling_settings_rest_normal_cases_without_overwrite.feature',
          'Change throttling settings for REST API Gateway with ForceExecution=False and '
          'with provided stage name')
def test_change_throttling_settings_rest_without_overwrite_and_with_provided_stage_name():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/change_throttling_settings_rest_normal_cases_with_overwrite.feature',
          'Change throttling settings for REST API Gateway with ForceExecution=True and without provided stage name')
def test_change_throttling_settings_rest_with_overwrite_and_without_provided_stage_name():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/change_throttling_settings_rest_normal_cases_with_overwrite.feature',
          'Change throttling settings for REST API Gateway with ForceExecution=True and with provided stage name')
def test_change_throttling_settings_rest_with_overwrite_and_with_provided_stage_name():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/change_throttling_settings_rest_normal_cases_with_overwrite.feature',
          'Change throttling settings for REST API Gateway with ForceExecution=True, without provided stage name and '
          'with new rate limit more than 50%')
def test_change_throttling_settings_rest_with_overwrite_with_provided_stage_name_and_with_new_rate_limit_more_than_50():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/change_throttling_settings_rest_failed_cases.feature',
          'Change throttling settings for REST API Gateway with ForceExecution=False and '
          'new rate limit more than 50%')
def test_change_throttling_settings_rest_without_overwrite_and_with_rate_limit_more_than_50():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/change_throttling_settings_rest_failed_cases.feature',
          'Change throttling settings for REST API Gateway with ForceExecution=False and '
          'new burst limit more than 50%')
def test_change_throttling_settings_rest_without_overwrite_and_with_new_burst_limit_more_than_50():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/change_throttling_settings_rest_failed_cases.feature',
          'Change throttling settings for REST API Gateway with ForceExecution=True and '
          'new rate limit more than account quota')
def test_change_throttling_settings_rest_with_overwrite_and_with_new_rate_limit_more_than_account_quota():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/change_throttling_settings_rest_failed_cases.feature',
          'Change throttling settings for REST API Gateway with ForceExecution=True and '
          'new burst limit more than account quota')
def test_change_throttling_settings_rest_with_overwrite_and_with_new_burst_limit_more_than_account_quota():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""
