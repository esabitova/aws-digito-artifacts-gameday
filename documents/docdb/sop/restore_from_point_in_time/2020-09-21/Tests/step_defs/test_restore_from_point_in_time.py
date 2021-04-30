# coding=utf-8
"""SSM automation document to restore a database from a Point in Time."""

from pytest_bdd import (
    scenario
)


@scenario('../features/restore_from_point_in_time.feature',
          'Recover the database into a known good state using latest point-in-time')
def test_restore_from_latest_point_in_time():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


# @scenario('../features/restore_from_point_in_time.feature',
#           'Recover the database into a known good state using earliest point-in-time')
# def test_restore_from_earliest_point_in_time():
#     """Create AWS resources using CloudFormation template and execute SSM automation document."""
