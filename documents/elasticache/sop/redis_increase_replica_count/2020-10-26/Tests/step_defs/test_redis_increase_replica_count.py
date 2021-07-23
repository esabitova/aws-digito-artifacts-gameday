
from pytest_bdd import scenario


@scenario('../features/redis_increase_replica_count_usual_case.feature',
          'Execute SSM automation document Digito-RedisIncreaseReplicaCount_2020-10-26 '
          'to increase redis replica count with Desired Replicas specified')
def test_redis_increase_replica_count_usual_case():
    """Execute SSM automation document Digito-RedisIncreaseReplicaCount_2020-10-26"""
