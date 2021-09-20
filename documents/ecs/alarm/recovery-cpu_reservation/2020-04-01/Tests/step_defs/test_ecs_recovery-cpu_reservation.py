# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/ecs_recovery-cpu_reservation.feature',
          'RecoveryCPUReservation - green')
def test_alarm_green():
    pass


@scenario('../features/ecs_recovery-cpu_reservation.feature',
          'RecoveryCPUReservation - red')
def test_alarm_red():
    pass
