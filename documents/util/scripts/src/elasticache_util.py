import logging
import time

import boto3
from distutils.version import LooseVersion


def check_required_params(required_params, events):
    for key in required_params:
        if key not in events:
            raise KeyError(f'Requires {key} in events')


def verify_all_nodes_in_rg_available(events, context):
    """
    Checks that replication group is in 'available' state and all nodes are in 'available' state
    :param events dict with the following keys
            * ReplicationGroupId (Required) - Id of replication group
            * Timeout (Optional) - time to wait for verifying
            * Sleep (Optional) - time to sleep between verification attempts
    :param context context
    """
    check_required_params(['ReplicationGroupId'], events)
    elasticache_client = boto3.client('elasticache')
    time_to_wait = events.get('Timeout', 900)
    time_to_sleep = int(events.get('Sleep', 15))
    timeout_timestamp = time.time() + int(time_to_wait)
    while time.time() < timeout_timestamp:
        rg = elasticache_client.describe_replication_groups(ReplicationGroupId=events['ReplicationGroupId'])
        status = rg['ReplicationGroups'][0]['Status']
        desired_members_count = len(rg['ReplicationGroups'][0]['MemberClusters'])
        available_members_count = len([x for x in rg['ReplicationGroups'][0]['NodeGroups'][0]['NodeGroupMembers']])
        logging.info(f'Expected {desired_members_count} members, got {available_members_count}')
        if status == 'available' and available_members_count == desired_members_count:
            return True
        time.sleep(time_to_sleep)
    raise TimeoutError(f'Replication group {events["ReplicationGroupId"]} couldn\'t '
                       f'be scaled in {time_to_wait} seconds')


def assert_cluster_mode_disabled(events, context):
    """
    Assert that cluster mode is disabled for given replication group
    """
    check_required_params(['ReplicationGroupId'], events)
    replication_group_id = events['ReplicationGroupId']
    elasticache_client = boto3.client('elasticache')
    cluster_mode = elasticache_client.describe_replication_groups(
        ReplicationGroupId=replication_group_id)['ReplicationGroups'][0]['ClusterEnabled']
    if cluster_mode:
        raise AssertionError('Cluster mode is enabled. '
                             'This automation is applicable only for replication group with "cluster mode" disabled')


def get_failover_settings(events, context):
    """
    Retrieves AutomaticFailover and MultiAZ settings in boolean format if they are in enabled or disabled state
    """
    check_required_params(['ReplicationGroupId'], events)
    replication_group_id = events['ReplicationGroupId']
    elasticache_client = boto3.client('elasticache')
    group_description = elasticache_client.describe_replication_groups(
        ReplicationGroupId=replication_group_id)['ReplicationGroups'][0]
    output = {}
    for setting in ['AutomaticFailover', 'MultiAZ']:
        if group_description[setting] == 'enabled':
            output[setting] = True
        elif group_description[setting] == 'disabled':
            output[setting] = False
        else:
            raise AssertionError(f'{setting} should be either in "enabled" or "disabled" state. '
                                 f'Current state is {group_description[setting]}')

    return output


def get_custom_parameter_group(events: dict, context: dict) -> dict:
    """
    Returns 'true' if Replication group has non-default CacheParameterGroup,
            'false' if Replication group has default CacheParameterGroup
    :param events: The dictionary that supposed to have the following keys:
      * ReplicationGroupId: name of Replication group
      * CustomCacheParameterGroupNamePostfix: unique string to generate a CacheParameterGroup name
      * ReservedMemoryPercent: value for reserved-memory-percent parameter
      * ReservedMemoryValue:value for reserved-memory parameter
    :param context:
    :return: Dict with key 'CacheParameterGroupExists' equals to 'true' if Replication group has
             non-default CacheParameterGroup, 'false' if Replication group has default CacheParameterGroup
    """
    required_params = [
        'ReplicationGroupId',
        'CustomCacheParameterGroupNamePostfix',
        'ReservedMemoryPercent',
        'ReservedMemoryValue'
    ]
    check_required_params(required_params, events)
    elasticache_client = boto3.client('elasticache')
    cluster_members = elasticache_client.describe_replication_groups(
        ReplicationGroupId=events['ReplicationGroupId']
    )['ReplicationGroups'][0]['MemberClusters']
    describe_cluster = elasticache_client.describe_cache_clusters(
        CacheClusterId=cluster_members[0]
    )['CacheClusters'][0]
    if LooseVersion(describe_cluster['EngineVersion']) < LooseVersion("3.2.4"):
        if events['ReservedMemoryPercent']:
            raise AssertionError(f'"reserved-memory-percent" parameter is supported only for Redis engine '
                                 f'with version higher than "3.2.4", got {describe_cluster["EngineVersion"]}.\n'
                                 f'Please remove `ReservedMemoryPercent` parameter '
                                 f'and add `ReservedMemoryValue` parameter')
        if not events['ReservedMemoryValue']:
            raise AssertionError(f'`ReservedMemoryValue` parameter is empty and replication group engine version '
                                 f'is {describe_cluster["EngineVersion"]} which supports only `ReservedMemoryValue`')

    res_cache_param_group_name = describe_cluster['CacheParameterGroup']['CacheParameterGroupName']
    res_cache_param_group = elasticache_client.describe_cache_parameter_groups(
        CacheParameterGroupName=res_cache_param_group_name
    )
    family = res_cache_param_group['CacheParameterGroups'][0]['CacheParameterGroupFamily']

    if res_cache_param_group_name.startswith('default.'):
        logging.info(f'Replication group {events["ReplicationGroupId"]} uses default parameter group, '
                     f'creating custom one...')
        return {
            "CacheParameterGroupExists": 'false',
            "CustomCacheParameterGroupName":
                f'{family.replace(".","-")}-{events["CustomCacheParameterGroupNamePostfix"]}',
            "CacheParameterGroupFamily": family
        }
    else:
        return {
            "CacheParameterGroupExists": 'true',
            "CustomCacheParameterGroupName": res_cache_param_group_name,
            "CacheParameterGroupFamily": family
        }


def wait_for_parameters_in_sync(events, context, elasticache_client=None,
                                time_to_wait=900, delay_sec=15):
    required_params = [
        'ReplicationGroupId'
    ]
    check_required_params(required_params, events)
    if not elasticache_client:
        elasticache_client = boto3.client('elasticache')

    cluster_members = elasticache_client.describe_replication_groups(
        ReplicationGroupId=events['ReplicationGroupId']
    )['ReplicationGroups'][0]['MemberClusters']
    cluster_members_left_to_check = cluster_members.copy()
    timeout_timestamp = time.time() + int(time_to_wait)
    while time.time() < timeout_timestamp and cluster_members_left_to_check:
        for cluster_member in cluster_members:
            status = elasticache_client.describe_cache_clusters(
                CacheClusterId=cluster_member
            )['CacheClusters'][0]['CacheParameterGroup']['ParameterApplyStatus']
            if status == 'in-sync':
                cluster_members_left_to_check.remove(cluster_member)
            else:
                logging.debug(f'Cluster {cluster_member} cache parameter group is still in status {status}')
        cluster_members = cluster_members_left_to_check
        time.sleep(delay_sec)
    if time.time() >= timeout_timestamp:
        raise TimeoutError(f"All CacheParameterGroups for replicas "
                           f"in rg {events['ReplicationGroupId']} didn't become available "
                           f"in {time_to_wait} seconds")


def modify_cache_parameter_group(events, context):
    required_params = [
        'CacheParameterGroupName',
        'ReservedMemoryValue',
        'ReservedMemoryPercent'
    ]
    check_required_params(required_params, events)
    elasticache_client = boto3.client('elasticache')
    if events['ReservedMemoryPercent']:
        kwargs = {
            "CacheParameterGroupName": events['CacheParameterGroupName'],
            "ParameterNameValues": [
                {
                    'ParameterName': 'reserved-memory-percent',
                    'ParameterValue': events['ReservedMemoryPercent']
                },
                {
                    'ParameterName': 'cluster-enabled',
                    'ParameterValue': 'yes'
                }
            ]
        }
    else:
        kwargs = {
            "CacheParameterGroupName": events['CacheParameterGroupName'],
            "ParameterNameValues": [
                {
                    'ParameterName': 'reserved-memory',
                    'ParameterValue': events['ReservedMemoryValue']
                },
                {
                    'ParameterName': 'cluster-enabled',
                    'ParameterValue': 'yes'
                }
            ]
        }

    elasticache_client.modify_cache_parameter_group(**kwargs)


def get_cache_parameter_group(events, context, elasticache_client=None) -> str:
    """
    gets cache parameter group attached to replication group
    :param events: The dictionary that supposed to have the following keys:
      * ReplicationGroupId: name of Replication group
    :param context context
    :param elasticache_client boto3 elasticache client to use from resource_manager
    :return: cache parameter group name
    """
    required_params = [
        'ReplicationGroupId'
    ]
    check_required_params(required_params, events)
    if not elasticache_client:
        elasticache_client = boto3.client('elasticache')
    replication_group = elasticache_client.describe_replication_groups(
        ReplicationGroupId=events['ReplicationGroupId']
    )  # will throw ClientError if replication_group doesn't exist
    cache_group_name = elasticache_client.describe_cache_clusters(
        CacheClusterId=replication_group['ReplicationGroups'][0]['MemberClusters'][0]
    )
    return cache_group_name['CacheClusters'][0]['CacheParameterGroup']['CacheParameterGroupName']
