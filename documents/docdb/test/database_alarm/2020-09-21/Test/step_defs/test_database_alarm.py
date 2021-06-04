# coding=utf-8
"""SSM automation document to test database alarm."""
from pytest_bdd import (
    scenario
)


@scenario('../features/database_alarm.feature',
          'Test database alarm')
def test_database_alarm(stop_canary_teardown):
    """Create AWS resources using CloudFormation template and execute SSM automation document."""
