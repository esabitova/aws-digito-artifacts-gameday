# coding=utf-8

from pytest_bdd import (
    scenario
)


@scenario('../features/queue_state_failure_dlq_standard.feature',
          'Create AWS resources using CloudFormation template and execute SSM automation document to test behavior of '
          'standard queue after receiving a message maximum allowed times')
def test_queue_state_failure_dlq_standard():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""
