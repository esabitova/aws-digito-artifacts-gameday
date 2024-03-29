# coding=utf-8

from pytest_bdd import (
    scenario
)


@scenario('../features/queue_max_receive_failure_standard.feature',
          'Create AWS resources using CloudFormation template and execute SSM automation document to test behavior of '
          'standard queue after receiving a message maximum allowed times')
def test_queue_max_receive_failure_standard():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/queue_max_receive_failure_standard_rollback_previous.feature',
          'Create AWS resources using CloudFormation template and execute SSM automation document to test rollback '
          'of previous execution')
def test_queue_max_receive_failure_standard_rollback_previous():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""
