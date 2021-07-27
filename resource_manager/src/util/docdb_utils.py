import time

import botocore
from boto3 import Session

import resource_manager.src.constants as constants
from .boto3_client_factory import client
from botocore.exceptions import ClientError


def get_number_of_instances(session: Session, db_cluster_identifier: str):
    """
    Use describe_db_instances aws method to get a list of DocDB instances, filter by 'available' status
     and return their amount
    :param session boto3 client session
    :param db_cluster_identifier DocDB cluster ID
    :return Number of DocDB available instances in cluster
    """
    docdb_client = client('docdb', session)
    response = docdb_client.describe_db_instances(Filters=[
        {
            'Name': 'db-cluster-id',
            'Values': [db_cluster_identifier]
        },
    ])
    number_of_instances = 0
    if response['DBInstances']:
        for db_instance in response['DBInstances']:
            if db_instance['DBInstanceStatus'] == 'available':
                number_of_instances += 1
    return number_of_instances


def get_instance_status(session: Session, db_instance_identifier: str):
    docdb = client('docdb', session)
    response = docdb.describe_db_instances(DBInstanceIdentifier=db_instance_identifier)
    if not response.get('DBInstances'):
        raise AssertionError('No DocumentDB instance found with identifier = %s' % db_instance_identifier)
    current_instance_status = response.get('DBInstances')[0].get('DBInstanceStatus')
    return {'DBInstanceStatus': current_instance_status}


def get_instance_az(session: Session, db_instance_identifier: str):
    """
    Use describe_db_instances aws method to get a Availability Zone of DocDB instance
    :param session boto3 client session
    :param db_instance_identifier DocDB instance ID
    :return Availability Zone of DocDB instance
    """
    docdb_client = client('docdb', session)
    response = docdb_client.describe_db_instances(DBInstanceIdentifier=db_instance_identifier)
    return response['DBInstances'][0]['AvailabilityZone']


def get_cluster_azs(session: Session, db_cluster_identifier: str):
    """
    Use describe_db_clusters aws method to get cluster's AvailabilityZones
    :param session boto3 client session
    :param db_cluster_identifier DocDB cluster ID
    :return Availability Zones of cluster
    """
    docdb_client = client('docdb', session)
    response = docdb_client.describe_db_clusters(DBClusterIdentifier=db_cluster_identifier)
    return response['DBClusters'][0]['AvailabilityZones']


def delete_instance(session: Session, db_instance_identifier: str):
    """
    Use delete_db_instance aws method to remove cluster's AvailabilityZones
    :param session boto3 client session
    :param db_instance_identifier DocDB cluster ID
    :return Availability Zones of cluster
    """
    docdb_client = client('docdb', session)
    try:
        response = docdb_client.delete_db_instance(DBInstanceIdentifier=db_instance_identifier)
    except ClientError as error:
        """
        To safely use this method in teardown let's ignore missing instances
        because tests can fail before instance was created
        """
        if error.response['Error']['Code'] == 'DBInstanceNotFound':
            return None
    waiter = docdb_client.get_waiter('db_instance_deleted')
    waiter.wait(
        DBInstanceIdentifier=db_instance_identifier
    )
    return response['DBInstance']['DBInstanceIdentifier']


def get_cluster_members(session: Session, db_cluster_identifier: str):
    """
    Use describe_db_clusters aws method to get a list of DocDB cluster members
    :param session boto3 client session
    :param db_cluster_identifier DocDB cluster ID
    :return Array of DocDB cluster members
    """
    docdb_client = client('docdb', session)
    response = docdb_client.describe_db_clusters(DBClusterIdentifier=db_cluster_identifier)
    return response['DBClusters'][0]['DBClusterMembers']


def get_cluster_instances(session: Session, db_cluster_identifier: str):
    """
    Use describe_db_instances aws method to get a list of DocDB instances
     and return their amount
    :param session boto3 client session
    :param db_cluster_identifier DocDB cluster ID
    :return DocDB instances in cluster
    """
    docdb_client = client('docdb', session)
    response = docdb_client.describe_db_instances(Filters=[
        {
            'Name': 'db-cluster-id',
            'Values': [db_cluster_identifier]
        },
    ])
    return response['DBInstances']


def delete_cluster(session: Session, db_cluster_identifier: str, wait: bool = True, time_to_wait: int = 300):
    """
    Use delete_db_cluster aws method to delete DocDB cluster
    :param session boto3 client session
    :param db_cluster_identifier DocDB cluster ID
    :param wait waiting for cluster deletion
    :param time_to_wait time to wait for cluster deletion if wait=True
    """
    docdb_client = client('docdb', session)
    docdb_client.delete_db_cluster(
        DBClusterIdentifier=db_cluster_identifier,
        SkipFinalSnapshot=True
    )
    if wait:
        is_cluster_deleted = False
        start_time = time.time()
        elapsed_time = time.time() - start_time
        while not is_cluster_deleted:
            if elapsed_time > int(time_to_wait):
                raise TimeoutError(f'Waiting for cluster deletion {db_cluster_identifier} timed out')
            time.sleep(constants.sleep_time_secs)
            elapsed_time = time.time() - start_time
            try:
                describe_response = docdb_client.describe_db_clusters(DBClusterIdentifier=db_cluster_identifier)
                is_cluster_deleted = describe_response['DBClusters'] and len(describe_response['DBClusters'][0]) == 0
            except Exception as error:
                if isinstance(error, botocore.exceptions.ClientError) and \
                        error.response['Error']['Code'] == 'DBClusterNotFoundFault':
                    is_cluster_deleted = True
                else:
                    raise error


def describe_cluster(session: Session, db_cluster_identifier: str):
    """
    Use describe_db_clusters aws method to get cluster's info
    :param session boto3 client session
    :param db_cluster_identifier DocDB cluster ID
    :return cluster info
    """
    docdb_client = client('docdb', session)
    response = docdb_client.describe_db_clusters(DBClusterIdentifier=db_cluster_identifier)
    return response['DBClusters'][0]


def create_snapshot(session: Session, db_cluster_identifier: str, snapshot_identifier: str):
    """
    Use create_db_cluster_snapshot aws method to create a cluster snapshot
    :param session boto3 client session
    :param db_cluster_identifier DocDB cluster ID
    :param snapshot_identifier new snapshot ID
    :return snapshotID
    """
    docdb_client = client('docdb', session)
    response = docdb_client.create_db_cluster_snapshot(
        DBClusterIdentifier=db_cluster_identifier,
        DBClusterSnapshotIdentifier=snapshot_identifier
    )
    return response['DBClusterSnapshot']['DBClusterSnapshotIdentifier']


def delete_snapshot(session: Session, snapshot_identifier: str):
    """
    Use delete_db_cluster_snapshot aws method to delete cluster snapshot
    :param session boto3 client session
    :param snapshot_identifier new snapshot ID
    :return snapshotID
    """
    docdb_client = client('docdb', session)
    try:
        response = docdb_client.delete_db_cluster_snapshot(
            DBClusterSnapshotIdentifier=snapshot_identifier
        )
    except ClientError as error:
        if error.response['Error']['Code'] == 'DBClusterSnapshotNotFoundFault':
            return None
    return response['DBClusterSnapshot']['DBClusterSnapshotIdentifier']


def is_snapshot_available(session: Session, snapshot_identifier: str):
    """
    Use describe_db_cluster_snapshots aws method to check is cluster snapshot available
    :param session boto3 client session
    :param snapshot_identifier snapshot ID
    :return Boolean, is snapshot status is available
    """
    docdb_client = client('docdb', session)
    response = docdb_client.describe_db_cluster_snapshots(
        DBClusterSnapshotIdentifier=snapshot_identifier
    )
    return response['DBClusterSnapshots'][0]['Status'] == 'available'


def delete_cluster_instances(session: Session, db_cluster_identifier, wait: bool = True, time_to_wait: int = 300):
    """
    Use delete_db_instance aws method to delete cluster instances
    :param session boto3 client session
    :param db_cluster_identifier cluster ID
    :param wait waiting for cluster deletion
    :param time_to_wait time to wait for cluster deletion if wait=True
    :return None
    """
    docdb_client = client('docdb', session)
    cluster_members = get_cluster_members(session, db_cluster_identifier)
    for cluster_member in cluster_members:
        instance_id = cluster_member['DBInstanceIdentifier']
        docdb_client.delete_db_instance(DBInstanceIdentifier=instance_id)
    if wait:
        start_time = time.time()
        elapsed_time = time.time() - start_time
        number_of_cluster_members = len(get_cluster_members(session, db_cluster_identifier))
        while number_of_cluster_members > 0:
            if elapsed_time > int(time_to_wait):
                raise TimeoutError(f'Waiting for instances deletion in cluster {db_cluster_identifier} timed out')
            time.sleep(constants.sleep_time_secs)
            number_of_cluster_members = len(get_cluster_members(session, db_cluster_identifier))
            elapsed_time = time.time() - start_time


def get_cluster_vpc_security_groups(session: Session, db_cluster_identifier: str):
    """
    Use describe_db_clusters aws method to get cluster's VpcSecurityGroups
    :param session boto3 client session
    :param db_cluster_identifier DocDB cluster ID
    :return Vpc Security Group Ids of cluster
    """
    docdb_client = client('docdb', session)
    response = docdb_client.describe_db_clusters(DBClusterIdentifier=db_cluster_identifier)
    return [security_group['VpcSecurityGroupId'] for security_group in response['DBClusters'][0]['VpcSecurityGroups']]
