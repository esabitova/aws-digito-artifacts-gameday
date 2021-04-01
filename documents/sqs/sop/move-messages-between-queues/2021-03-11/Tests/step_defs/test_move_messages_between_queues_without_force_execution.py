# coding=utf-8
"""SSM automation document to move messages from one queue to another"""

from pytest_bdd import (
    scenario
)


@scenario('../features/move_messages_between_queues_without_force_execution.feature',
          'Move messages from Standard queue to the other FIFO queue with ForceExecution = false')
def test_move_messages_from_standard_queue_to_fifo_with_error():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/move_messages_between_queues_without_force_execution.feature',
          'Move messages from FIFO queue to the other standard queue with ForceExecution = false')
def test_move_messages_from_fifo_queue_to_standard_with_error():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""
