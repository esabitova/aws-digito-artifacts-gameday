# coding=utf-8
"""SSM automation document to recover the database into a known good state."""

from pytest_bdd import (
    scenario
)


@scenario('../features/docdb_restore_from_backup.feature',
          'Recover the database into a known good state using latest snapshot')
def test_docdb_restore_from_latest_backup():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/docdb_restore_from_backup.feature',
          'Recover the database into a known good state using specified snapshot identifier')
def test_docdb_restore_from_specified_backup():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""
