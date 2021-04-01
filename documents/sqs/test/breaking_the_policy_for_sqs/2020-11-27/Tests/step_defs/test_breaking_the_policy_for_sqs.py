# coding=utf-8

from pytest_bdd import (
    scenario
)


@scenario('../features/breaking_the_policy_for_sqs.feature',
          'Create AWS resources using CloudFormation template and execute SSM automation document to test behavior '
          'when messages cannot be sent to an SQS queue')
def test_breaking_the_policy_for_sqs():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/breaking_the_policy_for_sqs_failed.feature',
          'Create AWS resources using CloudFormation template and execute SSM automation document to test behavior '
          'when messages cannot be sent to an SQS queue')
def test_breaking_the_policy_for_sqs_failed():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""
