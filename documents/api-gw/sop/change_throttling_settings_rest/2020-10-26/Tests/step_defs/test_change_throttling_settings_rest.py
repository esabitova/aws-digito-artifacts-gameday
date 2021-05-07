# coding=utf-8
"""SSM automation document to change REST API GW usage plan limits"""
from pytest_bdd import (
    scenario
)


@scenario('../features/change_throttling_settings_rest.feature',
          'Change throttling settings for REST API Gateway with ForceExecution=False and '
          'without provided stage name')
def test_change_throttling_settings_rest_without_overwrite_and_without_provided_stage_name():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""
