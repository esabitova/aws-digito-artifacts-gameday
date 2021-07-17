import time


def count_replicas_in_replication_group(session, replication_group_id):
    """
    Counts amount of nodes with 'replica' role in the first nodegroup of replication group
    :param session boto3 client session
    :param replication_group_id ID of the replication group
    """
    elasticache_client = session.client('elasticache')
    rg = elasticache_client.describe_replication_groups(
        ReplicationGroupId=replication_group_id
    )
    amount_of_replicas = len([x for x in rg['ReplicationGroups'][0]['NodeGroups'][0]['NodeGroupMembers']
                              if x['CurrentRole'] == 'replica'])
    return amount_of_replicas


def wait_for_available_status_on_rg_and_replicas(session, replication_group_id, timeout=900):
    """
    wait until RG is in 'available' status and all replicas become 'available'
    :param session boto3 client session
    :param replication_group_id ID of the replication group
    :param timeout timeout to wait for replica to be created
    """
    elasticache_client = session.client('elasticache')
    timeout_timestamp = time.time() + int(timeout)
    while time.time() < timeout_timestamp:
        rg = elasticache_client.describe_replication_groups(
            ReplicationGroupId=replication_group_id
        )
        status = rg['ReplicationGroups'][0]['Status']
        available_members_count = len([x for x in rg['ReplicationGroups'][0]['NodeGroups'][0]['NodeGroupMembers']])
        members_count = len([x for x in rg['ReplicationGroups'][0]['MemberClusters']])
        if status == 'available' and available_members_count == members_count:
            return True
        time.sleep(15)
    raise TimeoutError(f'Replication group {replication_group_id} couldn\'t '
                       f'be scaled in {timeout} seconds')


def increase_replicas_in_replication_group(session, replication_group_id, desired_count: int, timeout=900):
    """
    Increases amount of nodes with 'replica' role in the first nodegroup of replication group
    :param session boto3 client session
    :param replication_group_id ID of the replication group
    :param timeout timeout to wait for replica to be created
    :param desired_count Desired count of replicas
    """
    elasticache_client = session.client('elasticache')
    elasticache_client.increase_replica_count(
        ReplicationGroupId=replication_group_id,
        NewReplicaCount=desired_count,
        ApplyImmediately=True
    )
    wait_for_available_status_on_rg_and_replicas(session, replication_group_id, timeout)


def decrease_replicas_in_replication_group(session, replication_group_id, desired_count: int, timeout=900):
    """
    Decreases amount of nodes with 'replica' role in the first nodegroup of replication group
    :param session boto3 client session
    :param replication_group_id ID of the replication group
    :param timeout timeout to wait for replica to be deleted
    :param desired_count Desired count of replicas
    """
    elasticache_client = session.client('elasticache')
    elasticache_client.decrease_replica_count(
        ReplicationGroupId=replication_group_id,
        NewReplicaCount=desired_count,
        ApplyImmediately=True
    )
    wait_for_available_status_on_rg_and_replicas(session, replication_group_id, timeout)
