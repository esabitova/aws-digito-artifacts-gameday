# coding=utf-8

from pytest_bdd import (
    scenario
)


@scenario('../features/consume_more_rcu.feature',
          'Test that alarm detects when DynamoDB has read throttling events')
def test_consume_more_rcu():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""
