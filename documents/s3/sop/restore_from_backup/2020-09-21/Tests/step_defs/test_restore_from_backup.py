# coding=utf-8
"""SSM automation document to restore an S3 bucket from a backup bucket"""

from pytest_bdd import (
    scenario
)


@scenario('../features/restore_from_backup.feature',
          'Create AWS resources using CloudFormation template '
          'and execute SSM automation document to restore an S3 bucket from a backup bucket '
          'without approval to clean the restore bucket')
def test_restore_from_backup():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/restore_from_backup_approval.feature',
          'Create AWS resources using CloudFormation template '
          'and execute SSM automation document to restore an S3 bucket from a backup bucket '
          'with an approval to clean the restore bucket')
def test_restore_from_backup_approval():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/restore_from_backup_reject.feature',
          'Create AWS resources using CloudFormation template '
          'and execute SSM automation document to restore an S3 bucket from a backup bucket '
          'with a reject to clean the restore bucket')
def test_restore_from_backup_reject():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""
