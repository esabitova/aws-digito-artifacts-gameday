import json
import logging
import random
import time

import pytest
from pytest_bdd import (
    given, parsers, when, then
)

from resource_manager.src.util import elasticache_utils, common_test_utils, param_utils
from resource_manager.src.util.boto3_client_factory import client
from resource_manager.src.util.common_test_utils import (
    extract_param_value, put_to_ssm_test_cache
)
from resource_manager.src.util.elasticache_utils import do_create_elasticache_snapshot

logger = logging.getLogger(__name__)

cache_primary_and_replica_cluster_ids_expression = 'cache PrimaryClusterId and ReplicaClusterId "{step_key}" ' \
                                                   'SSM automation execution' \
                                                   '\n{input_parameters}'


@given(parsers.parse(cache_primary_and_replica_cluster_ids_expression))
@when(parsers.parse(cache_primary_and_replica_cluster_ids_expression))
@then(parsers.parse(cache_primary_and_replica_cluster_ids_expression))
def cache_primary_and_replica_cluster_ids_for_cluster_mode_disabled(resource_pool, ssm_test_cache, boto3_session,
                                                                    step_key, input_parameters):
    """
    Applicable only for Redis (cluster mode disabled) replication groups.
    Cache primary cluster id and last replica cluster id.
    """
    elasticache_client = client('elasticache', boto3_session)
    replication_group_id = extract_param_value(input_parameters, 'ReplicationGroupId', resource_pool, ssm_test_cache)
    group_description = elasticache_client.describe_replication_groups(ReplicationGroupId=replication_group_id)
    node_group_members = group_description['ReplicationGroups'][0]['NodeGroups'][0]['NodeGroupMembers']
    for node_group_member in node_group_members:
        try:
            # CurrentRole is obligatory for Redis (cluster mode disabled) replication groups
            if node_group_member['CurrentRole'] == 'primary':
                put_to_ssm_test_cache(ssm_test_cache, step_key, 'PrimaryClusterId', node_group_member['CacheClusterId'])
            else:
                put_to_ssm_test_cache(ssm_test_cache, step_key, 'ReplicaClusterId', node_group_member['CacheClusterId'])
        except KeyError as e:
            logger.error(f'CurrentRole property can be retrieved only from '
                         f'Redis (cluster mode disabled) replication groups: {e}')


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
def cache_replica_node_ids(resource_pool, ssm_test_cache, boto3_session, cache_property, step_key, input_parameters):
    elasticache_client = client('elasticache', boto3_session)
    replication_group_id = extract_param_value(input_parameters, 'ReplicationGroupId', resource_pool, ssm_test_cache)
    groups_description = elasticache_client.describe_replication_groups(ReplicationGroupId=replication_group_id)
    node_group_members = groups_description['ReplicationGroups'][0]['NodeGroups'][0]['NodeGroupMembers']
    node_id_list = [x['CacheClusterId'] for x in node_group_members if x['CurrentRole'] == 'replica']
    node_id = random.choice(node_id_list)
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, node_id)


@given(parsers.parse('cache replication group settings as "{cache_property}" '
                     '"{step_key}" SSM automation execution\n{input_parameters}'))
@then(parsers.parse('cache replication group settings as "{cache_property}" '
                    '"{step_key}" SSM automation execution\n{input_parameters}'))
def cache_replication_group_settings(resource_pool, ssm_test_cache, boto3_session, cache_property,
                                     step_key, input_parameters):
    settings_list = ['AtRestEncryptionEnabled',
                     'AutomaticFailover',
                     'ClusterEnabled',
                     'CacheNodeType',
                     'KmsKeyId',
                     'MultiAZ',
                     'TransitEncryptionEnabled']
    replication_group_id = extract_param_value(input_parameters, 'ReplicationGroupId', resource_pool, ssm_test_cache)
    elasticache_client = client('elasticache', boto3_session)
    group_description = elasticache_client.describe_replication_groups(
        ReplicationGroupId=replication_group_id)['ReplicationGroups'][0]
    settings_to_cache = {x: group_description[x] for x in settings_list}
    settings_to_cache['NumNodeGroups'] = len(group_description['NodeGroups'])
    settings_to_cache['NumMemberClusters'] = len(group_description['MemberClusters'])

    cluster_description = elasticache_client.describe_cache_clusters(
        CacheClusterId=group_description['MemberClusters'][0])['CacheClusters'][0]
    settings_to_cache['CacheSubnetGroupName'] = cluster_description['CacheSubnetGroupName']
    settings_to_cache['SecurityGroupIds'] = [sg['SecurityGroupId'] for sg in cluster_description['SecurityGroups']]
    logging.info(f'Cache replication group settings as {cache_property} {step_key}: {settings_to_cache}')
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, settings_to_cache)


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


@given(parsers.parse('extract ReshardingConfiguration from "{node_groups_ref}" '
                     'NodeGroups as "{cache_property}" to "{step_key}"'))
@then(parsers.parse('extract ReshardingConfiguration from "{node_groups_ref}" '
                    'NodeGroups as "{cache_property}" to "{step_key}"'))
def extract_resharding_configuration(resource_pool, ssm_test_cache, boto3_session, node_groups_ref, cache_property,
                                     step_key):
    node_groups = param_utils.parse_param_value(node_groups_ref, {'cache': ssm_test_cache})
    resharding_configuration = [{"NodeGroupId": node_group['NodeGroupId'],
                                 "PreferredAvailabilityZones": [member['PreferredAvailabilityZone']
                                                                for member in node_group['NodeGroupMembers']]
                                 } for node_group in node_groups]

    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, resharding_configuration)


@given(parsers.parse('destring "{resharding_configuration_ref}" ReshardingConfiguration '
                     'as "{cache_property}" to "{step_key}"'))
@then(parsers.parse('destring "{resharding_configuration_ref}" ReshardingConfiguration '
                    'as "{cache_property}" to "{step_key}"'))
def destring_resharding_configuration(resource_pool, ssm_test_cache, boto3_session, resharding_configuration_ref,
                                      cache_property,
                                      step_key):
    resharding_configuration = param_utils.parse_param_value(resharding_configuration_ref, {'cache': ssm_test_cache})
    resharding_configuration_destringed = [json.loads(config) for config in resharding_configuration]

    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, resharding_configuration_destringed)


@when(parsers.parse('generate new ReshardingConfiguration '
                    'as "{cache_property}" "{step_key}"\n{input_parameters}'))
@given(parsers.parse('generate new ReshardingConfiguration '
                     'as "{cache_property}" "{step_key}"\n{input_parameters}'))
def generate_resharding_configuration(resource_pool, ssm_test_cache, boto3_session, cache_property, step_key,
                                      input_parameters):
    """
    Generate ReshardingConfiguration based on PreferredAvailabilityZones with new additional item in the end
    """
    current_resharding_configuration = common_test_utils.extract_param_value(input_parameters,
                                                                             'CurrentReshardingConfiguration',
                                                                             resource_pool, ssm_test_cache)
    new_shard_count = common_test_utils.extract_param_value(input_parameters, 'NewShardCount',
                                                            resource_pool, ssm_test_cache)

    # Copy existing PreferredAvailabilityZones to the new configuration
    resharding_configuration = [json.dumps(configuration) for configuration in current_resharding_configuration]

    # Create PreferredAvailabilityZones for new shards by picking random availability zones
    diff_shard_count = new_shard_count - len(current_resharding_configuration)
    azs = []
    node_group_members_number = 0
    for configuration in current_resharding_configuration:
        preferred_availability_zones = configuration['PreferredAvailabilityZones']
        node_group_members_number = len(preferred_availability_zones)
        azs.extend(preferred_availability_zones)
    unique_azs = set(azs)

    for i in range(diff_shard_count):
        remained_unique_azs = list(unique_azs)
        new_preferred_availability_zones = []
        for _ in range(node_group_members_number):
            az = random.choice(remained_unique_azs)
            new_preferred_availability_zones.append(az)
        resharding_configuration_item = json.dumps({"NodeGroupId": str(len(resharding_configuration) + 1).zfill(4),
                                                    "PreferredAvailabilityZones": new_preferred_availability_zones})
        resharding_configuration.append(resharding_configuration_item)

    common_test_utils.put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, resharding_configuration)


@given(parsers.parse('create snapshot and cache as "{cache_property}" '
                     '"{step_key}" SSM automation execution\n{input_parameters}'))
def create_snapshot(resource_pool, ssm_test_cache, boto3_session, delete_snapshot, cache_property, step_key,
                    input_parameters):
    replication_group_id = extract_param_value(input_parameters, 'ReplicationGroupId', resource_pool, ssm_test_cache)
    elasticache_client = client('elasticache', boto3_session)
    snapshot_name = 'redis-snapshot-' + str(round(time.time()))
    delete_snapshot['SnapshotName'] = snapshot_name

    do_create_elasticache_snapshot(boto3_session, cache_property, elasticache_client, replication_group_id,
                                   ssm_test_cache, step_key, snapshot_name)


@given(parsers.parse('generate replication group ID and cache as "{cache_property}" '
                     '"{step_key}" SSM automation execution'))
def generate_replication_group_id(ssm_test_cache, cache_property, step_key, delete_replication_group):
    replication_group_id = 'redis-' + str(round(time.time()))
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, replication_group_id)
    delete_replication_group['ReplicationGroupId'] = replication_group_id


@pytest.fixture(scope='function')
def delete_replication_group(ssm_test_cache, boto3_session):
    delete_replication_group = {}
    yield delete_replication_group
    replication_group_id = delete_replication_group['ReplicationGroupId']
    logging.info('Start replication group teardown ...')
    if elasticache_utils.check_replication_group_exists(boto3_session, replication_group_id):
        elasticache_utils.delete_replication_group(boto3_session, replication_group_id, wait_for_deletion=True)
    else:
        logging.warning(f'Replication group {replication_group_id} not found! Skip replication group teardown')


@pytest.fixture(scope='function')
def delete_snapshot(ssm_test_cache, boto3_session):
    delete_snapshot = {}
    yield delete_snapshot
    snapshot_name = delete_snapshot['SnapshotName']
    logging.info('Start snapshot teardown ...')
    if elasticache_utils.check_snapshot_exists(boto3_session, snapshot_name):
        elasticache_utils.delete_snapshot(boto3_session, snapshot_name, wait_for_deletion=True)
    else:
        logging.warning(f'Snapshot "{snapshot_name}" not found! Skip snapshot teardown')


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


@given(parsers.parse('cache CacheParameterGroupName as "{cache_property}"\n{input_parameters}'))
def cache_cache_parameter_group(boto3_session, resource_pool, ssm_test_cache, cache_property, input_parameters):
    replication_group_id = extract_param_value(input_parameters, 'ReplicationGroupId', resource_pool, ssm_test_cache)
    cache_parameter_group_name = elasticache_utils.get_cache_parameter_group(boto3_session, replication_group_id)
    ssm_test_cache[cache_property] = str(cache_parameter_group_name)


@pytest.fixture(scope='function')
def delete_cache_parameter_group(boto3_session):
    delete_param_group_dict = {}
    yield delete_param_group_dict

    elasticache_utils.delete_cache_parameter_group(boto3_session,
                                                   cache_param_group=delete_param_group_dict[
                                                       'CustomCacheParameterGroupName'],
                                                   replication_group_id=delete_param_group_dict['ReplicationGroupId'],
                                                   old_cache_param_group=delete_param_group_dict[
                                                       'OldCacheParameterGroupName'])


@then(parsers.parse('assert "{expected_property}" at "{step_key_for_expected}" '
                    'became equal to "{actual_property}" at "{step_key_for_actual}" '
                    'without order of PreferredAvailabilityZones'))
def assert_equal(ssm_test_cache, expected_property, step_key_for_expected, actual_property, step_key_for_actual):
    expected_resharding_configuration = ssm_test_cache[step_key_for_expected][expected_property]
    actual_resharding_configuration = ssm_test_cache[step_key_for_actual][actual_property]

    for config in expected_resharding_configuration:
        config['PreferredAvailabilityZones'] = sorted(config['PreferredAvailabilityZones'])
    for config in actual_resharding_configuration:
        config['PreferredAvailabilityZones'] = sorted(config['PreferredAvailabilityZones'])

    assert expected_resharding_configuration == actual_resharding_configuration
