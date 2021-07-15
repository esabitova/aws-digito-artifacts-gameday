import boto3


def check_required_params(required_params, events):
    for key in required_params:
        if key not in events:
            raise KeyError(f'Requires {key} in events')


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
