# coding=utf-8

from pytest_bdd import (
    scenario
)


@scenario('../features/block_delete_message_usual_case.feature',
          'Create AWS resources using CloudFormation template and execute SSM automation document to block '
          'sqs:DeleteMessage')
def test_block_delete_message_usual_case():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""
