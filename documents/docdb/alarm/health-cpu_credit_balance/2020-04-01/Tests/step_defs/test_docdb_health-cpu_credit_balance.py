# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/docdb_health-cpu_credit_balance.feature',
          'To detect low values of CPUCreditBalance - red')
def test_docdb_health_cpu_credit_balance_alarm_red():
    pass


@scenario('../features/docdb_health-cpu_credit_balance.feature',
          'To detect low values of CPUCreditBalance - green')
def test_docdb_health_cpu_credit_balance_alarm_green():
    pass
