# coding=utf-8
"""SSM automation document to recover the database into a known good state."""

from pytest_bdd import (
    scenario
)


@scenario('../features/docdb_restore_from_backup.feature',
          'Create AWS resources using CloudFormation template and execute SSM automation document to recover the database into a known good state')
def test_docdb_restore_from_backup():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""