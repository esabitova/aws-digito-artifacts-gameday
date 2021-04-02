# coding=utf-8

from pytest_bdd import (
    scenario
)


@scenario('../features/block_delete_message_usual_case.feature',
          'Create AWS resources using CloudFormation template and execute SSM automation document to block '
          'sqs:DeleteMessage')
def test_block_delete_message_usual_case():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/block_delete_message_failed.feature',
          'Create AWS resources using CloudFormation template and execute SSM automation document to block '
          'sqs:DeleteMessage')
def test_block_delete_message_failed():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/block_delete_message_rollback_previous.feature',
          'Create AWS resources using CloudFormation template and execute SSM automation document to block '
          'sqs:DeleteMessage')
def test_block_delete_message_rollback_previous():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/block_delete_message_fifo_usual_case.feature',
          'Create AWS resources using CloudFormation template and execute SSM automation document to block '
          'sqs:DeleteMessage')
def test_block_delete_message_fifo_usual_case():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/block_delete_message_fifo_failed.feature',
          'Create AWS resources using CloudFormation template and execute SSM automation document to block '
          'sqs:DeleteMessage')
def test_block_delete_message_fifo_failed():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/block_delete_message_fifo_rollback_previous.feature',
          'Create AWS resources using CloudFormation template and execute SSM automation document to block '
          'sqs:DeleteMessage')
def test_block_delete_message_fifo_rollback_previous():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""
