# coding=utf-8
"""SSM automation document to reboot DB instance."""

from pytest_bdd import (
    scenario
)


@scenario('../features/restore_from_backup.feature',
          'Restores table from backup')
def test_restore_from_backup():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/restore_from_backup.feature',
          'Restores table from backup. Stream Enabled')
def test_restore_from_backup_stream_enabled():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/restore_from_backup.feature',
          'Restores table from backup. Kinesis Enabled')
def test_restore_from_backup_kinesis_enabled():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/restore_from_backup.feature',
          'Restores table from backup. Contributor Insights')
def test_restore_from_backup_contributor_insights():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/restore_from_backup.feature',
          'Restores table from backup. With Autoscaling')
def test_restore_from_backup_auto_scaling():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/restore_from_backup.feature',
          'Restores table from backup. Global Table')
def test_restore_from_backup_global_table():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/restore_from_backup.feature',
          'Restores table from backup with TTL enabled')
def test_restore_from_backup_with_ttl_enabled():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/restore_from_backup.feature',
          'Restores table to the latest available point. Copy Alarms')
def test_restore_from_backup_copy_alarms():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""
