from boto3 import Session
from .boto3_client_factory import client


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
    response = docdb_client.delete_db_instance(DBInstanceIdentifier=db_instance_identifier)
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


def delete_cluster(session: Session, db_cluster_identifier: str):
    """
    Use delete_db_cluster aws method to delete DocDB cluster
    :param session boto3 client session
    :param db_cluster_identifier DocDB cluster ID
    """
    docdb_client = client('docdb', session)
    docdb_client.delete_db_cluster(
        DBClusterIdentifier=db_cluster_identifier,
        SkipFinalSnapshot=True
    )


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
