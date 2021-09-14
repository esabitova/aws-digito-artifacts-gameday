import logging

import pytest
from pytest_bdd import scenario

from resource_manager.src.util.boto3_client_factory import client

logger = logging.getLogger(__name__)


@scenario('../features/redis_increase_shards_usual_case.feature',
          'Execute SSM automation document Digito-RedisIncreaseShards_2020-10-26 without ReshardingConfiguration')
def test_redis_increase_shards_usual_case_empty_resharding_configuration():
    """Execute SSM automation document Digito-RedisIncreaseShards_2020-10-26"""


@scenario('../features/redis_increase_shards_usual_case.feature',
          'Execute SSM automation document Digito-RedisIncreaseShards_2020-10-26 with ReshardingConfiguration')
def test_redis_increase_shards_usual_case_non_empty_resharding_configuration():
    """Execute SSM automation document Digito-RedisIncreaseShards_2020-10-26"""


@pytest.fixture(scope='function', autouse=True)
def revert_resharding(boto3_session, ssm_test_cache):
    yield
    replication_group_id = ssm_test_cache['before']['ReplicationGroupId']
    node_groups_to_retain = [node_group['NodeGroupId'] for node_group in ssm_test_cache['before']['NodeGroups']]
    node_group_count = ssm_test_cache['before']['NodeGroupIdsSize']
    logger.info(f'Trying to revert the ReshardingConfiguration by execution of '
                f'modify_replication_group_shard_configuration with arguments:'
                f'ApplyImmediately=True, '
                f'ReplicationGroupId={replication_group_id}, '
                f'NodeGroupsToRetain={node_groups_to_retain}, '
                f'NodeGroupCount={node_group_count}')
    elasticache_client = client('elasticache', boto3_session)
    elasticache_client.modify_replication_group_shard_configuration(ApplyImmediately=True,
                                                                    ReplicationGroupId=replication_group_id,
                                                                    NodeGroupsToRetain=node_groups_to_retain,
                                                                    NodeGroupCount=node_group_count)

    waiter = elasticache_client.get_waiter('replication_group_available')
    logger.info(f'Waiting for ReplicationGroup {replication_group_id} being available...')
    waiter.wait(ReplicationGroupId=replication_group_id,
                WaiterConfig={'Delay': 20, 'MaxAttempts': 120})
    logger.info(f'ReplicationGroup {replication_group_id} become available')
