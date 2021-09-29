import logging
import time

from botocore.exceptions import ClientError

import documents.util.scripts.src.elasticache_util as elasticache_util
from resource_manager.src.util.boto3_client_factory import client
from resource_manager.src.util.common_test_utils import put_to_ssm_test_cache

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def count_replicas_in_replication_group(session, replication_group_id):
    """
    Counts amount of nodes with 'replica' role in the first nodegroup of replication group
    :param session boto3 client session
    :param replication_group_id ID of the replication group
    """
    elasticache_client = client('elasticache', session)
    rg = elasticache_client.describe_replication_groups(
        ReplicationGroupId=replication_group_id
    )
    amount_of_replicas = len([x for x in rg['ReplicationGroups'][0]['NodeGroups'][0]['NodeGroupMembers']
                              if x['CurrentRole'] == 'replica'])
    return amount_of_replicas


def check_replication_group_exists(session, replication_group_id):
    """
    Check if Replication Group exists by its ID and return appropriate boolean value
    :param session: The boto3 client session
    :param replication_group_id: The Id of Replication Group
    :return: True: If Replication Group exists
             False: If Replication Group does not exist
    """
    try:
        elasticache_client = client('elasticache', session)
        elasticache_client.describe_replication_groups(ReplicationGroupId=replication_group_id)
        return True
    except ClientError as error:
        if error.response['Error']['Code'] == 'ReplicationGroupNotFoundFault':
            return False
        logging.error(error)
        raise error


def check_snapshot_exists(session, snapshot_name):
    """
    Check if Snapshot exists by its name and return appropriate boolean value
    :param session: The boto3 client session
    :param snapshot_name: The name of Snapshot
    :return: True: If Snapshot exists
             False: If Snapshot does not exist
    """
    elasticache_client = client('elasticache', session)
    snapshots = elasticache_client.describe_snapshots(SnapshotName=snapshot_name)['Snapshots']
    return bool(snapshots)


def delete_replication_group(session, replication_group_id, wait_for_deletion, delay=20, max_attempts=30):
    """
    Wait for "available" status and then delete Replication Group. Optionally waits until deletion will be completed
    :param session: The boto3 client session
    :param replication_group_id: The Id of Replication Group
    :param wait_for_deletion: If True then method will wait until deletion will be completed
    :param delay: The amount of time in seconds to wait between attempts. Default: 20
    :param max_attempts: The maximum number of attempts to be made. Default: 30
    """
    wait_for_replication_group_available(session, replication_group_id, delay, max_attempts)
    logging.info(f'Delete replication group "{replication_group_id}" ...')
    elasticache_client = client('elasticache', session)
    response = elasticache_client.delete_replication_group(
        ReplicationGroupId=replication_group_id)['ReplicationGroup']
    logging.info(f'Replication group "{replication_group_id}" in status "{response["Status"]}"')
    if wait_for_deletion:
        wait_for_replication_group_deleted(session, replication_group_id, delay, max_attempts)


def delete_snapshot(session, snapshot_name, wait_for_deletion, delay=20, max_attempts=30):
    """
    Wait for 'available' status and then delete Snapshot. Optionally waits until deletion will be completed
    :param session: The boto3 client session
    :param snapshot_name: The name of the snapshot
    :param wait_for_deletion: If True then method will wait until deletion will be completed
    :param delay: The amount of time in seconds to wait between attempts. Default: 20
    :param max_attempts: The maximum number of attempts to be made. Default: 30
    """
    wait_for_snapshot_available(session, snapshot_name, delay, max_attempts)
    logging.info(f'Delete snapshot "{snapshot_name}" ...')
    elasticache_client = client('elasticache', session)
    response = elasticache_client.delete_snapshot(SnapshotName=snapshot_name)['Snapshot']
    logging.info(f'Snapshot "{snapshot_name}" in status "{response["SnapshotStatus"]}"')
    if wait_for_deletion:
        wait_for_snapshot_deleted(session, snapshot_name, delay, max_attempts)


def wait_for_available_status_on_rg_and_replicas(session, replication_group_id,
                                                 timeout=900, sleep=15):
    """
    Wait until RG is in 'available' status and all replicas become 'available'
    :param session boto3 client session
    :param replication_group_id ID of the replication group
    :param timeout timeout to wait for replica to be created
    :param sleep:  time to sleep between API calls
    """
    elasticache_client = client('elasticache', session)
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
        time.sleep(sleep)
    raise TimeoutError(f'Replication group {replication_group_id} couldn\'t '
                       f'be scaled in {timeout} seconds')


def wait_for_cache_cluster_available(session, cache_cluster_id, delay=20, max_attempts=30):
    """
    Wait until Replication Group will be in available status
    :param session: The boto3 client session
    :param cache_cluster_id: The Id of Cache Cluster
    :param delay: The amount of time in seconds to wait between attempts. Default: 20
    :param max_attempts: The maximum number of attempts to be made. Default: 30
    """
    elasticache_client = client('elasticache', session)
    waiter = elasticache_client.get_waiter('cache_cluster_available')
    logging.info(f'Waiting for CacheCluster {cache_cluster_id} in status "available" ...')
    waiter.wait(CacheClusterId=cache_cluster_id, WaiterConfig={'Delay': delay, 'MaxAttempts': max_attempts})
    logging.info(f'CacheCluster {cache_cluster_id} status "available"')


def wait_for_replication_group_available(session, replication_group_id, delay=20, max_attempts=30):
    """
    Wait until Replication Group will be in 'available' status
    :param session: The boto3 client session
    :param replication_group_id: The Id of Replication Group
    :param delay: The amount of time in seconds to wait between attempts. Default: 20
    :param max_attempts: The maximum number of attempts to be made. Default: 30
    """
    elasticache_client = client('elasticache', session)
    waiter = elasticache_client.get_waiter('replication_group_available')
    logging.info(f'Waiting for Replication Group {replication_group_id} in status "available" ...')
    waiter.wait(ReplicationGroupId=replication_group_id, WaiterConfig={'Delay': delay, 'MaxAttempts': max_attempts})
    logging.info(f'Replication Group {replication_group_id} status "available"')


def wait_for_replication_group_deleted(session, replication_group_id, delay=20, max_attempts=30):
    """
    Wait until Replication Group will be deleted
    :param session: The boto3 client session
    :param replication_group_id: The Id of Replication Group
    :param delay: The amount of time in seconds to wait between attempts. Default: 20
    :param max_attempts: The maximum number of attempts to be made. Default: 30
    """
    elasticache_client = client('elasticache', session)
    waiter = elasticache_client.get_waiter('replication_group_deleted')
    logging.info(f'Waiting for deletion of Replication Group {replication_group_id} ...')
    waiter.wait(ReplicationGroupId=replication_group_id, WaiterConfig={'Delay': delay, 'MaxAttempts': max_attempts})
    logging.info(f'Replication Group {replication_group_id} deleted')


def wait_for_snapshot_available(session, snapshot_name, delay=20, max_attempts=30):
    """
    Wait until Snapshot will be in 'available' status
    :param session: The boto3 client session
    :param snapshot_name: The name of the snapshot
    :param delay: The amount of time in seconds to wait between attempts.
    :param max_attempts: The maximum number of attempts to be made.
    """
    elasticache_client = client('elasticache', session)
    timeout = delay * max_attempts
    while max_attempts > 0:
        status = elasticache_client.describe_snapshots(SnapshotName=snapshot_name)['Snapshots'][0]['SnapshotStatus']
        if status == 'available':
            logging.info(f'Snapshot "{snapshot_name}" in status "available"')
            return
        logging.debug(f'Waiting for snapshot "{snapshot_name}" status "available". Actual status "{status}"')
        time.sleep(delay)
        max_attempts -= 1
    raise TimeoutError(f'Timeout {str(timeout)} seconds exceeded during waiting '
                       f'for Snapshot {snapshot_name} in status "available"')


def wait_for_snapshot_deleted(session, snapshot_name, delay=20, max_attempts=30):
    """
    Wait until Snapshot will be deleted
    :param session: The boto3 client session
    :param snapshot_name: The name of the snapshot
    :param delay: The amount of time in seconds to wait between attempts.
    :param max_attempts: The maximum number of attempts to be made.
    """
    logging.info(f'Waiting for deletion of Snapshot "{snapshot_name}" ...')
    timeout = delay * max_attempts
    while max_attempts > 0:
        if not check_snapshot_exists(session, snapshot_name):
            logging.info(f'Snapshot "{snapshot_name}" deleted')
            return
        logging.debug(f'Waiting for snapshot "{snapshot_name}" will be deleted')
        time.sleep(delay)
        max_attempts -= 1
    raise TimeoutError(f'Timeout "{str(timeout)}" seconds exceeded during waiting '
                       f'for Snapshot "{snapshot_name}" will be deleted')


def increase_replicas_in_replication_group(session, replication_group_id, desired_count: int, timeout=900):
    """
    Increases amount of nodes with 'replica' role in the first nodegroup of replication group
    :param session boto3 client session
    :param replication_group_id ID of the replication group
    :param timeout timeout to wait for replica to be created
    :param desired_count Desired count of replicas
    """
    elasticache_client = client('elasticache', session)
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
    elasticache_client = client('elasticache', session)
    elasticache_client.decrease_replica_count(
        ReplicationGroupId=replication_group_id,
        NewReplicaCount=desired_count,
        ApplyImmediately=True
    )
    wait_for_available_status_on_rg_and_replicas(session, replication_group_id, timeout)


def get_cache_parameter_group(session, replication_group_id: str) -> str:
    """
    gets cache parameter group attached to replication group
    will throw ClientError if replication_group doesn't exist
    :param session boto3 client session
    :param replication_group_id ID of the replication group
    :return: cache parameter group name
    """
    elasticache_client = session.client('elasticache')
    return elasticache_util.get_cache_parameter_group({'ReplicationGroupId': replication_group_id},
                                                      {},
                                                      elasticache_client)


def wait_for_parameters_in_sync(session, replication_group_id, time_to_wait=900, delay_sec=15):
    elasticache_client = session.client('elasticache')
    elasticache_util.wait_for_parameters_in_sync(
        events={'ReplicationGroupId': replication_group_id},
        context={},
        elasticache_client=elasticache_client,
        time_to_wait=time_to_wait,
        delay_sec=delay_sec
    )


def delete_cache_parameter_group(session, cache_param_group: str,
                                 replication_group_id: str, old_cache_param_group: str) -> None:
    """
    Changes CacheParameterGroup for replication group to an old one and removes specified CacheParameterGroup
    :param session: boto3 client session
    :param cache_param_group: Name of CacheParameterGroup to delete
    :param replication_group_id: ID of the replication group
    :param old_cache_param_group: Name of CacheParameterGroup to set for ReplicationGroup
    :return:
    """
    elasticache_client = session.client('elasticache')
    wait_for_parameters_in_sync(session, replication_group_id)
    elasticache_client.modify_replication_group(
        CacheParameterGroupName=old_cache_param_group,
        ReplicationGroupId=replication_group_id,
        ApplyImmediately=True
    )

    elasticache_client.delete_cache_parameter_group(
        CacheParameterGroupName=cache_param_group
    )


def do_create_elasticache_snapshot(boto3_session, cache_property, elasticache_client,
                                   replication_group_id,
                                   ssm_test_cache, step_key, snapshot_name):
    snapshot_params = {'SnapshotName': snapshot_name}

    group_description = elasticache_client.describe_replication_groups(
        ReplicationGroupId=replication_group_id)['ReplicationGroups'][0]

    cluster_enabled = group_description['ClusterEnabled']
    if cluster_enabled:
        snapshot_params['ReplicationGroupId'] = replication_group_id
        wait_for_replication_group_available(boto3_session, replication_group_id)
    else:
        cache_cluster_id = group_description['MemberClusters'][0]
        snapshot_params['CacheClusterId'] = cache_cluster_id
        wait_for_cache_cluster_available(boto3_session, cache_cluster_id)

    logging.info(f'Create snapshot "{snapshot_name}" with params: {snapshot_params} ...')
    snapshot = elasticache_client.create_snapshot(**snapshot_params)['Snapshot']
    logging.info(f'Snapshot "{snapshot_name}" in status "{snapshot["SnapshotStatus"]}"')

    logging.info(f'Waiting for "{snapshot["SnapshotStatus"]}" status of the "{snapshot_name}"')
    wait_for_snapshot_available(boto3_session, snapshot_name)
    logging.info(f'Snapshot "{snapshot_name}" became available')

    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, snapshot_name)
