import logging
import random

import pytest
from pytest_bdd import (
    given, parsers, when, then
)

from resource_manager.src.util import elasticache_utils
from resource_manager.src.util.boto3_client_factory import client
from resource_manager.src.util.common_test_utils import (
    extract_param_value, put_to_ssm_test_cache
)

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
        if node_group_member.get('CurrentRole') == 'primary':
            put_to_ssm_test_cache(ssm_test_cache, step_key, 'PrimaryClusterId', node_group_member['CacheClusterId'])
        else:
            put_to_ssm_test_cache(ssm_test_cache, step_key, 'ReplicaClusterId', node_group_member['CacheClusterId'])


cache_failover_settings_expression = 'cache FailoverSettings "{step_key}" SSM automation execution' \
                                     '\n{input_parameters}'


@given(parsers.parse(cache_failover_settings_expression))
@when(parsers.parse(cache_failover_settings_expression))
@then(parsers.parse(cache_failover_settings_expression))
def cache_failover_settings(resource_pool, ssm_test_cache, boto3_session, step_key, input_parameters):
    elasticache_client = client('elasticache', boto3_session)
    replication_group_id = extract_param_value(input_parameters, 'ReplicationGroupId', resource_pool, ssm_test_cache)
    group_description = elasticache_client.describe_replication_groups(
        ReplicationGroupId=replication_group_id)['ReplicationGroups'][0]
    failover_settings = {
        'ReplicationGroupId': replication_group_id,
        'AutomaticFailover': group_description['AutomaticFailover'],
        'MultiAZ': group_description['MultiAZ']
    }
    put_to_ssm_test_cache(ssm_test_cache, step_key, 'FailoverSettings', failover_settings)


register_failover_settings_for_teardown_expression = 'register FailoverSettings for teardown'


@given(parsers.parse(register_failover_settings_for_teardown_expression))
def register_failover_settings_for_teardown(ssm_test_cache, revert_failover_settings):
    failover_settings = ssm_test_cache['before']['FailoverSettings']
    revert_failover_settings['ReplicationGroupId'] = failover_settings['ReplicationGroupId']
    revert_failover_settings['AutomaticFailover'] = failover_settings['AutomaticFailover']
    revert_failover_settings['MultiAZ'] = failover_settings['MultiAZ']


cache_replica_node_id_expression = 'cache random replica node ID as "{cache_property}" ' \
                                   '"{step_key}" SSM automation execution' \
                                   '\n{input_parameters}'


@given(parsers.parse(cache_replica_node_id_expression))
def cache_replica_node_id(resource_pool, ssm_test_cache, boto3_session, cache_property, step_key, input_parameters):
    elasticache_client = boto3_session.client('elasticache')
    replication_group_id = extract_param_value(input_parameters, 'ReplicationGroupId', resource_pool, ssm_test_cache)
    groups_description = elasticache_client.describe_replication_groups(ReplicationGroupId=replication_group_id)
    node_group_members = groups_description['ReplicationGroups'][0]['NodeGroups'][0]['NodeGroupMembers']
    node_id_list = [x['CacheClusterId'] for x in node_group_members if x['CurrentRole'] == 'replica']
    node_id = random.choice(node_id_list)
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, node_id)


register_replica_count_for_teardown_expression = 'register redis replication group replica count for teardown' \
                                                 '\n{input_parameters}'


@when(parsers.parse(register_replica_count_for_teardown_expression))
@given(parsers.parse(register_replica_count_for_teardown_expression))
def register_replica_count_for_teardown(resource_pool, ssm_test_cache, boto3_session,
                                        revert_replica_count, input_parameters):
    replication_group_id = extract_param_value(input_parameters, 'ReplicationGroupId', resource_pool, ssm_test_cache)
    amount_of_replicas = elasticache_utils.count_replicas_in_replication_group(boto3_session, replication_group_id)
    revert_replica_count['replication_group_id'] = replication_group_id
    revert_replica_count['old_amount_of_replicas'] = amount_of_replicas
    logger.debug(f'Cleanup for ReplicationGroupId: {replication_group_id} registered')


cache_replica_count_expression = 'cache replica count as "{cache_property}" "{step_key}" SSM automation execution' \
                                 '\n{input_parameters}'


@given(parsers.parse(cache_replica_count_expression))
@then(parsers.parse(cache_replica_count_expression))
def cache_replica_count(resource_pool, ssm_test_cache, boto3_session, cache_property, step_key, input_parameters):
    replication_group_id = extract_param_value(input_parameters, 'ReplicationGroupId', resource_pool, ssm_test_cache)
    amount_of_replicas = elasticache_utils.count_replicas_in_replication_group(boto3_session, replication_group_id)
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, amount_of_replicas)


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
        logger.debug("Scaling down...")
        elasticache_utils.decrease_replicas_in_replication_group(boto3_session,
                                                                 replication_group_dict['replication_group_id'],
                                                                 replication_group_dict['old_amount_of_replicas'])
    elif int(replication_group_dict['old_amount_of_replicas']) > int(amount_of_replicas):
        logger.debug("Scaling up...")
        elasticache_utils.increase_replicas_in_replication_group(boto3_session,
                                                                 replication_group_dict['replication_group_id'],
                                                                 replication_group_dict['old_amount_of_replicas'])
    else:
        logger.debug("scaling not needed")


@pytest.fixture(scope='function')
def revert_failover_settings(boto3_session):
    failover_settings_before = {}
    yield failover_settings_before
    replication_group_id = failover_settings_before.pop('ReplicationGroupId')
    elasticache_utils.wait_for_replication_group_available(boto3_session, replication_group_id)
    elasticache_client = client('elasticache', boto3_session)
    group_description = elasticache_client.describe_replication_groups(
        ReplicationGroupId=replication_group_id)['ReplicationGroups'][0]
    failover_settings_after = {x: group_description[x] for x in ['AutomaticFailover', 'MultiAZ']}
    if failover_settings_before != failover_settings_after:
        logging.warning(f'Failover settings before {failover_settings_before} not equal'
                        f' to settings after {failover_settings_after}')
        logging.info(f'Reverting failover setting with params: {failover_settings_before}')
        automatic_failover_enabled = failover_settings_before['AutomaticFailover'] == 'enabled'
        multi_az_enabled = failover_settings_before['MultiAZ'] == 'enabled'
        response = elasticache_client.modify_replication_group(ApplyImmediately=True,
                                                               ReplicationGroupId=replication_group_id,
                                                               AutomaticFailoverEnabled=automatic_failover_enabled,
                                                               MultiAZEnabled=multi_az_enabled)['ReplicationGroup']
        logging.info(f'Replication group status: {response["Status"]}, '
                     f'AutomaticFailover: {response["AutomaticFailover"]}, '
                     f'MultiAZ:  {response["MultiAZ"]}')
    else:
        logging.info('Skip failover settings teardown')
