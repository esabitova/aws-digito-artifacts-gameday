# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/redshift_cluster_health_status.feature',
          'Lease redshift from resource manager and test attach an alarm from Document')
def test_redshift_cluster_health_status():
    pass
