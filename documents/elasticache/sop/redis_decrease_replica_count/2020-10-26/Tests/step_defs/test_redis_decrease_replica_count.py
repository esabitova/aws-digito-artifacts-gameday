from pytest_bdd import scenario


@scenario('../features/redis_decrease_replica_count_usual_case.feature',
          'Execute SSM automation document Digito-RedisDecreaseReplicaCount_2020-10-26 '
          'to decrease redis replica count with node ids for replicas specified')
def test_redis_decrease_replica_count_usual_case():
    """Execute SSM automation document Digito-RedisDecreaseReplicaCount_2020-10-26"""


@scenario('../features/redis_decrease_replica_count_new_replica_count.feature',
          'Execute SSM automation document Digito-RedisDecreaseReplicaCount_2020-10-26 '
          'to decrease redis replica count with Desired Replicas specified')
def test_redis_decrease_replica_count_new_replica_count():
    """Execute SSM automation document Digito-RedisDecreaseReplicaCount_2020-10-26"""
