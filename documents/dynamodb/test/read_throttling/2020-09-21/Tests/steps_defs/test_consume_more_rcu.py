# coding=utf-8

from pytest_bdd import (
    scenario
)


@scenario('../features/read_throttling.feature',
          'Test that alarm detects when DynamoDB has read throttling events')
def test_read_throttling():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/read_throttling_failed.feature',
          'Execute SSM automation document Digito-ForceDynamoDbTableReadThrottlingTest_2020-09-21 to test failure case')
def test_read_throttling_failed():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/read_throttling_rollback_previous.feature',
          'Execute SSM automation document Digito-ForceDynamoDbTableReadThrottlingTest_2020-09-21 in rollback')
def test_read_throttling_rollback_previous():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""
