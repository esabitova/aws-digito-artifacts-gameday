# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/redshift_maintenance_mode.feature',
          'Create redshift:alarm:maintenance_mode:2020-04-01 '
          'based on MaintenanceMode metric and check OK status')
def test_redshift_maintenance_mode():
    pass
