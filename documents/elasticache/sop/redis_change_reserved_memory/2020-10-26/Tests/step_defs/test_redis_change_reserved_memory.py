
from pytest_bdd import scenario


@scenario('../features/redis_change_reserved_memory_usual_case.feature',
          'Execute SSM automation document Digito-ElasticacheRedisChangeReservedMemorySOP_2020-10-26 '
          'without CustomCacheParameterGroup')
def test_redis_change_reserved_memory_usual_case():
    pass
