# coding=utf-8

from pytest_bdd import (
    scenario,
)


@scenario('../features/dynamodb_recovery-replication_latency.feature',
          'Replication Latency - green')
def test_dynamodb_recovery_replication_latency_alarm_green():
    pass


@scenario('../features/dynamodb_recovery-replication_latency.feature',
          'Replication Latency - red')
def test_dynamodb_recovery_replication_latency_alarm_red():
    pass
