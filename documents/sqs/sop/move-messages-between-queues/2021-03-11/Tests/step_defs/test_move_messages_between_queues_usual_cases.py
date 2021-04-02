# coding=utf-8
"""SSM automation document to move messages from one queue to another"""

from pytest_bdd import (
    scenario
)


@scenario('../features/move_messages_between_queues_usual_cases.feature',
          'Move messages from Standard queue to the other FIFO queue')
def test_move_messages_from_standard_queue_to_fifo(cache):
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/move_messages_between_queues_usual_cases.feature',
          'Move messages from Standard queue to the other Standard queue')
def test_move_messages_from_standard_queue_to_standard():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/move_messages_between_queues_usual_cases.feature',
          'Move messages from Standard queue to the other Standard queue with a lot of messages')
def test_move_messages_from_standard_queue_to_standard_with_a_lot_of_messages():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/move_messages_between_queues_usual_cases.feature',
          'Move messages from FIFO queue to the other standard queue')
def test_move_messages_from_fifo_queue_to_standard():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/move_messages_between_queues_usual_cases.feature',
          'Move messages from FIFO queue to the other FIFO queue')
def test_move_messages_from_fifo_queue_to_fifo():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""
