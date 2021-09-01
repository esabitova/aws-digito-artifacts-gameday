# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/health_master_link_health_status.feature',
          'Create elasticache:alarm:health-master_link_health_status:2020-04-01 '
          'based on MasterLinkHealthStatus and check OK status')
def test_elasticache_redis_master_link_health_status():
    pass
