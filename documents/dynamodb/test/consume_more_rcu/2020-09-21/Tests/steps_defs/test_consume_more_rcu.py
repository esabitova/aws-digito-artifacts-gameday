# coding=utf-8

from pytest_bdd import (
    scenario
)


@scenario('../features/consume_more_rcu.feature',
          'Test that alarm detects when DynamoDB has read throttling events')
def test_consume_more_rcu():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""

#
# @scenario('../features/consume_more_rcu_failed.feature',
#           'Execute SSM automation document Digito-ConsumeMoreRCU_2020-09-21 to test failure case')
# def test_consume_more_rcu_failed():
#     """Create AWS resources using CloudFormation template and execute SSM automation document."""
#
#
# @scenario('../features/consume_more_rcu_rollback_previous.feature',
#           'Execute SSM automation document Digito-ConsumeMoreRCU_2020-09-21 in rollback')
# def test_consume_more_rcu_rollback_previous():
#     """Create AWS resources using CloudFormation template and execute SSM automation document."""
