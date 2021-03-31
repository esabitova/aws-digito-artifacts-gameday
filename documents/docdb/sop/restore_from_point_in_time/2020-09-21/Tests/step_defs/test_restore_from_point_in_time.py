# coding=utf-8
"""SSM automation document to restore a database from a Point in Time."""

from pytest_bdd import (
    scenario
)


@scenario('../features/restore_from_point_in_time.feature',
          'Create AWS resources using CloudFormation template and execute SSM automation document')
def test_restore_from_point_in_time():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""
