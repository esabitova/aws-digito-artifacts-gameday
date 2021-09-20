# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/ecs_recovery-memory_reservation.feature',
          'HighMemoryReservation - green')
def test_alarm_green():
    pass


@scenario('../features/ecs_recovery-memory_reservation.feature',
          'HighMemoryReservation - red')
def test_alarm_red():
    pass
