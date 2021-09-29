import json
import logging
import time
from distutils.version import LooseVersion

import boto3
from botocore.exceptions import ClientError

log = logging.getLogger()


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
        log.debug(f'Expected {desired_members_count} members, got {available_members_count}')
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
    cluster_enabled = elasticache_client.describe_replication_groups(
        ReplicationGroupId=replication_group_id)['ReplicationGroups'][0]['ClusterEnabled']
    if cluster_enabled:
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
                f'{family.replace(".", "-")}-{events["CustomCacheParameterGroupNamePostfix"]}',
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


def describe_snapshot_and_extract_settings(events, context):
    """
    Describes snapshot and retrieves settings from source cluster if exists
    """
    check_required_params(['SnapshotName'], events)
    snapshot_name = events['SnapshotName']
    settings_to_copy = ['AtRestEncryptionEnabled',
                        'KmsKeyId',
                        'TransitEncryptionEnabled']
    elasticache_client = boto3.client('elasticache')
    snapshot_description = elasticache_client.describe_snapshots(SnapshotName=snapshot_name)['Snapshots'][0]
    snapshot_create_time = snapshot_description['NodeSnapshots'][0]['SnapshotCreateTime']
    replication_group_id = snapshot_description.get('ReplicationGroupId')
    # If the source cluster was deleted then all possible source settings from the snapshot will be automatically
    # copied while restoring
    if replication_group_id:
        source_settings = get_setting_from_replication_group_cluster_enabled(
            elasticache_client, replication_group_id, settings_to_copy
        )
    else:
        cache_cluster_id = snapshot_description['CacheClusterId']
        source_settings = get_setting_from_replication_group_cluster_disabled(
            elasticache_client, cache_cluster_id, settings_to_copy
        )

    return {'SourceSettings': json.dumps(source_settings),
            'RecoveryPoint': snapshot_create_time.isoformat()}


def get_setting_from_replication_group_cluster_enabled(client, replication_group_id, settings):
    """
    Get list of 'settings' from Replication Group,
    get 'SecurityGroupIds', 'CacheSubnetGroupName' settings from Cache Cluster,
    if Replication Group exists
    :param client: Boto3(elasticache) client
    :param replication_group_id: The ID of Replication Group
    :param settings: The list of settings to get from Replication Group
    """
    group_description = describe_replication_group_if_exists(client, replication_group_id)
    if not group_description:
        return {}

    group_description = group_description['ReplicationGroups'][0]
    output = {
        x: group_description[x]
        for x in settings
        if group_description.get(x) is not None
    }
    cache_cluster_id = group_description['MemberClusters'][0]
    cluster_description = client.describe_cache_clusters(CacheClusterId=cache_cluster_id)['CacheClusters'][0]
    output['SecurityGroupIds'] = [x['SecurityGroupId'] for x in cluster_description['SecurityGroups']]
    output['CacheSubnetGroupName'] = cluster_description['CacheSubnetGroupName']

    return output


def get_setting_from_replication_group_cluster_disabled(client, cache_cluster_id, settings):
    """
    Get list of 'settings' from Replication Group,
    get 'AutomaticFailover' and 'MultiAZ' settings from Replication Group,
    get 'SecurityGroupIds', 'CacheSubnetGroupName' settings from Cache Cluster,
    calculate number of cache clusters in Replication Group,
    if Cache CLuster and Replication Group exist
    :param client: Boto3(elasticache) client
    :param cache_cluster_id: The ID of Cache Cluster
    :param settings: The list of settings to get from Replication Group
    """
    cluster_description = describe_cache_cluster_if_exists(client, cache_cluster_id)
    if not cluster_description:
        # If source Replication Group (cluster mode disabled) is not available,
        # we use recommended number of cache clusters (1 primary and 2 replicas) by default.
        # Otherwise create_replication_group API call will create Replication Group (cluster mode disabled)
        # from snapshot, with only 1 node (CacheCluster)
        return {'NumCacheClusters': 3}

    cluster_description = cluster_description['CacheClusters'][0]
    output = {
        'SecurityGroupIds': [x['SecurityGroupId'] for x in cluster_description['SecurityGroups']],
        'CacheSubnetGroupName': cluster_description['CacheSubnetGroupName']
    }
    replication_group_id = cluster_description['ReplicationGroupId']
    group_description = client.describe_replication_groups(
        ReplicationGroupId=replication_group_id)['ReplicationGroups'][0]
    output['NumCacheClusters'] = len(group_description['MemberClusters'])
    # It is not needed for the "cluster mode enabled" case since it is copying automatically from a snapshot during
    # creation of replication group from a snapshot
    for x in ['AutomaticFailover', 'MultiAZ']:
        if group_description.get(x) is not None:
            output[x + 'Enabled'] = group_description[x] in ['enabled', 'enabling']

    for x in settings:
        if group_description.get(x) is not None:
            output[x] = group_description[x]

    return output


def describe_cache_cluster_if_exists(client, cache_cluster_id):
    """
    Describes Cache Cluster if exists by its ID
    :param client: The boto3 client
    :param cache_cluster_id: The ID of Cache Cluster
    """
    try:
        response = client.describe_cache_clusters(CacheClusterId=cache_cluster_id)
        log.info(f'Cache Cluster with ID "{cache_cluster_id}" found')
        return response

    except ClientError as error:
        if error.response['Error']['Code'] == 'CacheClusterNotFound':
            log.info(f'Cache Cluster with ID "{cache_cluster_id}" does not exist')
            return False
        log.error(error)
        raise error


def describe_replication_group_if_exists(client, replication_group_id):
    """
    Describes if Replication Group if exists by its ID
    :param client: The boto3 client
    :param replication_group_id: The ID of Replication Group
    """
    try:
        response = client.describe_replication_groups(ReplicationGroupId=replication_group_id)
        log.info(f'Replication Group with ID "{replication_group_id}" found')
        return response

    except ClientError as error:
        if error.response['Error']['Code'] == 'ReplicationGroupNotFoundFault':
            log.info(f'Replication Group with ID "{replication_group_id}" does not exist')
            return False
        log.error(error)
        raise error


def create_replication_group_from_snapshot(events, context):
    """
    Describes snapshot and retrieves settings from source cluster if exists
    """
    required_params = ['ReplicationGroupId',
                       'ReplicationGroupDescription',
                       'Settings',
                       'SnapshotName']
    check_required_params(required_params, events)
    kwargs = json.loads(events['Settings'])
    for argument in ['ReplicationGroupId', 'ReplicationGroupDescription', 'SnapshotName']:
        kwargs[argument] = events[argument]
    elasticache_client = boto3.client('elasticache')
    log.debug(f'Making API call create_replication_group with parameters: {kwargs}')
    response = elasticache_client.create_replication_group(**kwargs)['ReplicationGroup']
    log.debug(f'API call response: {response}')

    return {'ReplicationGroupARN': response['ARN']}
