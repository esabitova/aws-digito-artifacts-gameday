# coding=utf-8
"""SSM automation document clean up SQS queue"""

from pytest_bdd import (
    scenario
)


@scenario('../features/purge_queue.feature',
          'Create AWS resources using CloudFormation template and execute SSM automation document to clean up SQS '
          'queue without approval to clean the restore bucket')
def test_purge_queue():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""
