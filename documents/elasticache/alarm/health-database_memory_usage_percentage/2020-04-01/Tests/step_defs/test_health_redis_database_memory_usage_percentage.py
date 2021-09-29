# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/health_redis_database_memory_usage_percentage.feature',
          'Create elasticache:alarm:health-database_memory_usage_percentage:2020-04-01 '
          'based on DatabaseMemoryUsagePercentage metric and check OK status')
def test_elasticache_redis_database_memory_usage_percentage():
    pass
