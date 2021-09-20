# coding=utf-8

from pytest_bdd import (
    scenario
)


@scenario('../features/break_queue_policy.feature',
          'Create AWS resources using CloudFormation template and execute SSM automation document to test behavior '
          'when messages cannot be sent to an SQS queue')
def test_break_queue_policy():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/break_queue_policy_failed.feature',
          'Create AWS resources using CloudFormation template and execute SSM automation document to test behavior when'
          ' policy won\'t allow message sending but alarm isn\'t triggered')
def test_break_queue_policy_failed():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/break_queue_policy_rollback_previous.feature',
          'Create AWS resources using CloudFormation template and execute SSM automation document to test behavior '
          'when messages cannot be sent to an SQS queue')
def test_break_queue_policy_rollback_previous():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""
