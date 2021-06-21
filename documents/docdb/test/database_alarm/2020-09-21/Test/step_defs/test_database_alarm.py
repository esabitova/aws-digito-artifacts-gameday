# coding=utf-8
"""SSM automation document to test database alarm."""
from pytest_bdd import (
    scenario
)


@scenario('../features/database_alarm.feature',
          'Test database alarm')
def test_database_alarm(stop_canary_teardown):
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/database_alarm_rollback_previous.feature',
          'Test database alarm SSM execution in rollback')
def test_database_alarm_rollback_previous(stop_canary_teardown):
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/database_alarm_failed.feature',
          'Test database alarm SSM execution failure')
def test_database_alarm_failed(stop_canary_teardown):
    """Create AWS resources using CloudFormation template and execute SSM automation document."""
