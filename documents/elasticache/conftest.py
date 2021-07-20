import random

from pytest_bdd import (
    given,
    parsers, when, then
)
import logging
import pytest

from resource_manager.src.util.boto3_client_factory import client
from resource_manager.src.util.common_test_utils import extract_param_value
from resource_manager.src.util.common_test_utils import put_to_ssm_test_cache
from resource_manager.src.util import common_test_utils, elasticache_utils

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

cache_primary_and_replica_cluster_ids_expression = 'cache PrimaryClusterId and ReplicaClusterId "{step_key}" ' \
                                                   'SSM automation execution' \
                                                   '\n{input_parameters}'


@given(parsers.parse(cache_primary_and_replica_cluster_ids_expression))
@when(parsers.parse(cache_primary_and_replica_cluster_ids_expression))
@then(parsers.parse(cache_primary_and_replica_cluster_ids_expression))
def cache_primary_and_replica_cluster_ids(resource_pool, ssm_test_cache, boto3_session, step_key, input_parameters):
    elasticache_client = client('elasticache', boto3_session)
    replication_group_id = extract_param_value(input_parameters, 'ReplicationGroupId', resource_pool, ssm_test_cache)
    group_description = elasticache_client.describe_replication_groups(ReplicationGroupId=replication_group_id)
    node_group_members = group_description['ReplicationGroups'][0]['NodeGroups'][0]['NodeGroupMembers']
    for node_group_member in node_group_members:
        if node_group_member['CurrentRole'] == 'primary':
            put_to_ssm_test_cache(ssm_test_cache, step_key, 'PrimaryClusterId', node_group_member['CacheClusterId'])
        else:
            put_to_ssm_test_cache(ssm_test_cache, step_key, 'ReplicaClusterId', node_group_member['CacheClusterId'])


@given(parsers.parse('cache random replica node ID as "{cache_property}" '
                     '"{step_key}" SSM automation execution\n{input_parameters}'))
def cache_replica_node_id(resource_pool, ssm_test_cache, boto3_session, cache_property, step_key,
                          input_parameters):
    replication_group_id = common_test_utils.extract_param_value(input_parameters, 'ReplicationGroupId',
                                                                 resource_pool, ssm_test_cache)
    elasticache_client = boto3_session.client('elasticache')
    rg = elasticache_client.describe_replication_groups(
        ReplicationGroupId=replication_group_id
    )
    node_id_list = [x['CacheClusterId'] for x in rg['ReplicationGroups'][0]['NodeGroups'][0]['NodeGroupMembers']
                    if x['CurrentRole'] == 'replica']
    node_id = random.choice(node_id_list)
    common_test_utils.put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, node_id)


@when(parsers.parse('register redis replication group replica count for teardown\n{input_parameters}'))
@given(parsers.parse('register redis replication group replica count for teardown\n{input_parameters}'))
def register_replica_count_for_teardown(resource_pool, ssm_test_cache, boto3_session,
                                        revert_replica_count, input_parameters):
    replication_group_id = common_test_utils.extract_param_value(input_parameters, 'ReplicationGroupId',
                                                                 resource_pool, ssm_test_cache)
    amount_of_replicas = elasticache_utils.count_replicas_in_replication_group(boto3_session, replication_group_id)
    revert_replica_count['replication_group_id'] = replication_group_id
    revert_replica_count['old_amount_of_replicas'] = amount_of_replicas
    logger.debug(f'Cleanup for ReplicationGroupId: {replication_group_id} registered')


@given(parsers.parse('cache replica count as "{cache_property}" '
                     '"{step_key}" SSM automation execution\n{input_parameters}'))
@then(parsers.parse('cache replica count as "{cache_property}" '
                    '"{step_key}" SSM automation execution\n{input_parameters}'))
def cache_replica_count(resource_pool, ssm_test_cache, boto3_session, cache_property, step_key,
                        input_parameters):
    replication_group_id = common_test_utils.extract_param_value(input_parameters, 'ReplicationGroupId',
                                                                 resource_pool, ssm_test_cache)
    amount_of_replicas = elasticache_utils.count_replicas_in_replication_group(boto3_session, replication_group_id)
    common_test_utils.put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, amount_of_replicas)


@pytest.fixture(scope='function')
def revert_replica_count(boto3_session):
    replication_group_dict = {}
    yield replication_group_dict
    amount_of_replicas = elasticache_utils. \
        count_replicas_in_replication_group(boto3_session, replication_group_dict['replication_group_id'])
    logger.debug(f"Reverting replicas of replication group: {replication_group_dict['replication_group_id']} "
                 f"from {amount_of_replicas} "
                 f"to {replication_group_dict['old_amount_of_replicas']}")

    if int(replication_group_dict['old_amount_of_replicas']) < int(amount_of_replicas):
        logger.debug("scaling down...")
        elasticache_utils.decrease_replicas_in_replication_group(boto3_session,
                                                                 replication_group_dict['replication_group_id'],
                                                                 replication_group_dict['old_amount_of_replicas'])
    elif int(replication_group_dict['old_amount_of_replicas']) > int(amount_of_replicas):
        logger.debug("scaling up...")
        elasticache_utils.increase_replicas_in_replication_group(boto3_session,
                                                                 replication_group_dict['replication_group_id'],
                                                                 replication_group_dict['old_amount_of_replicas'])
    else:
        logger.debug("scaling not needed")
