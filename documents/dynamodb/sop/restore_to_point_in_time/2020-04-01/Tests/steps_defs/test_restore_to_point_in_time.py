# coding=utf-8
"""SSM automation document to reboot DB instance."""

from pytest_bdd import (
    scenario
)


@scenario('../features/restore_to_latest_point_in_time.feature',
          'Restores table to the latest available point')
def test_restore_to_latest_point_in_time():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/restore_to_latest_point_in_time.feature',
          'Restores table to the latest available point. '
          'In the source table the stream is enabled')
def test_restore_to_latest_point_in_time_stream_enabled():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/restore_to_specific_point_in_time.feature',
          'Restores table to the specific point')
def test_restore_to_specific_point_in_time():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""
