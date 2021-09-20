# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/ecs_recovery-gpu_reservation.feature',
          'HighGPUReservation - green')
def test_alarm_green():
    pass


@scenario('../features/ecs_recovery-gpu_reservation.feature',
          'HighGPUReservation - red')
def test_alarm_red():
    pass
