# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/redshift_cluster_health_status.feature',
          'Create redshift:alarm:cluster_health_status:2020-04-01 '
          'based on HealthStatus metric and check OK status')
def test_redshift_cluster_health_status():
    pass
