
from pytest_bdd import scenario


@scenario('../features/redis_decrease_replica_count_usual_case.feature',
          'Execute SSM automation document Digito-RedisDecreaseReplicaCount_2020-10-26')
def test_redis_decrease_replica_count_usual_case():
    """Execute SSM automation document Digito-RedisDecreaseReplicaCount_2020-10-26"""
