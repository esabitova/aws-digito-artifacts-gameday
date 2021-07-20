# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/dynamodb_recovery-pending_replication_count.feature',
          'pending_replication_count - green')
def test_alarm_green():
    pass
