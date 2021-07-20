import logging
import time
import boto3


def check_required_params(required_params, events):
    for key in required_params:
        if key not in events:
            raise KeyError(f'Requires {key} in events')


def verify_all_nodes_in_rg_available(events, context):
    """
    checks that replication group is in 'available' state and all nodes are in 'available' state
    :param events dict with the following keys
            * ReplicationGroupId (Required) - Id of replication group
            * Timeout (Optional) - time to wait for verifying
    :param context context
    """
    required_params = [
        'ReplicationGroupId'
    ]
    check_required_params(required_params, events)
    elasticache_client = boto3.client('elasticache')
    time_to_wait = events.get('Timeout', 900)
    timeout_timestamp = time.time() + int(time_to_wait)
    while time.time() < timeout_timestamp:
        rg = elasticache_client.describe_replication_groups(
            ReplicationGroupId=events['ReplicationGroupId']
        )
        status = rg['ReplicationGroups'][0]['Status']
        desired_members_count = len(rg['ReplicationGroups'][0]['MemberClusters'])
        available_members_count = len([x for x in rg['ReplicationGroups'][0]['NodeGroups'][0]['NodeGroupMembers']])
        logging.info(f'Expected {desired_members_count} members, got {available_members_count}')
        if status == 'available' and available_members_count == desired_members_count:
            return True
        time.sleep(15)
    raise TimeoutError(f'Replication group {events["ReplicationGroupId"]} couldn\'t '
                       f'be scaled in {time_to_wait} seconds')


def assert_cluster_mode_disabled(events, context):
    """
    Assert that cluster mode is disabled for given replication group
    """
    check_required_params(['ReplicationGroupId'], events)
    replication_group_id = events['ReplicationGroupId']
    elasticache_client = boto3.client('elasticache')
    node_groups = elasticache_client.describe_replication_groups(
        ReplicationGroupId=replication_group_id)['ReplicationGroups'][0]['NodeGroups']
    if len(node_groups) > 1:
        raise AssertionError('Cluster mode is enabled. '
                             'This SOP is applicable only for replication group with cluster mode disabled')


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
