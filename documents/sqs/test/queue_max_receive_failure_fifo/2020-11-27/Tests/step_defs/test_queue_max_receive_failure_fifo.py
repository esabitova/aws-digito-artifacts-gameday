# coding=utf-8

from pytest_bdd import (
    scenario
)


@scenario('../features/queue_max_receive_failure_fifo.feature',
          'Create AWS resources using CloudFormation template and execute SSM automation document to test behavior of '
          'FIFO queue after receiving a message maximum allowed times and move messages from DLQ afterwards')
def test_queue_max_receive_failure_fifo():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/queue_max_receive_failure_fifo_no_move.feature',
          'Create AWS resources using CloudFormation template and execute SSM automation document to test behavior of '
          'FIFO queue after receiving a message maximum allowed times')
def test_queue_max_receive_failure_fifo_no_move():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/queue_max_receive_failure_fifo_rollback_previous.feature',
          'Create AWS resources using CloudFormation template and execute SSM automation document to test '
          'rollback of a previous execution and move messages from DLQ')
def test_queue_max_receive_failure_fifo_rollback_previous():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/queue_max_receive_failure_fifo_rollback_previous_no_move.feature',
          'Create AWS resources using CloudFormation template and execute SSM automation document to test '
          'rollback of a previous execution')
def test_queue_max_receive_failure_fifo_rollback_previous_no_move():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""
