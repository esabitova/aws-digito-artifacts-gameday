# coding=utf-8
"""SSM automation document to reboot DB instance."""

from pytest_bdd import (
    scenario
)


@scenario('../features/restore_to_point_in_time.feature',
          'Create AWS resources using CloudFormation template and execute SSM automation document to restore '
          'the database to point in time')
def test_restore_to_point_in_time():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""
