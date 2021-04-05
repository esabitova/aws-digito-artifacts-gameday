# coding=utf-8

from pytest_bdd import (
    scenario
)


@scenario('../features/queue_state_failure_dlq_fifo.feature',
          'Create AWS resources using CloudFormation template and execute SSM automation document to test behavior of '
          'FIFO queue after receiving a message maximum allowed times and purge DLQ afterwards')
def test_queue_state_failure_dlq_fifo():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/queue_state_failure_dlq_fifo_no_purge.feature',
          'Create AWS resources using CloudFormation template and execute SSM automation document to test behavior of '
          'FIFO queue after receiving a message maximum allowed times')
def test_queue_state_failure_dlq_fifo_no_purge():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/queue_state_failure_dlq_fifo_rollback_previous.feature',
          'Create AWS resources using CloudFormation template and execute SSM automation document to test rollback '
          'after messages went to DLQ and purge it')
def test_queue_state_failure_dlq_fifo_rollback_previous():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/queue_state_failure_dlq_fifo_rollback_previous_no_purge.feature',
          'Create AWS resources using CloudFormation template and execute SSM automation document to test rollback '
          'after messages went to DLQ')
def test_queue_state_failure_dlq_fifo_rollback_previous_no_purge():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""
