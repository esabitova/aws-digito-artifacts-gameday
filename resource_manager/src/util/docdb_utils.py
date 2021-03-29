def get_number_of_instances(boto3_session, db_cluster_identifier: str):
    """
    Use describe_db_instances aws method to get a list of DocDB instances, filter by 'available' status
     and return their amount
    :param boto3_session boto3 client session
    :param db_cluster_identifier DocDB cluster ID
    :return Number of DocDB available instances in cluster
    """
    docdb_client = boto3_session.client('docdb')
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


def get_instance_az(boto3_session, db_instance_identifier: str):
    """
    Use describe_db_instances aws method to get a Availability Zone of DocDB instance
    :param boto3_session boto3 client session
    :param db_instance_identifier DocDB instance ID
    :return Availability Zone of DocDB instance
    """
    docdb_client = boto3_session.client('docdb')
    response = docdb_client.describe_db_instances(DBInstanceIdentifier=db_instance_identifier)
    return response['DBInstances'][0]['AvailabilityZone']


def get_cluster_azs(boto3_session, db_cluster_identifier: str):
    """
    Use describe_db_clusters aws method to get cluster's AvailabilityZones
    :param boto3_session boto3 client session
    :param db_cluster_identifier DocDB cluster ID
    :return Availability Zones of cluster
    """
    docdb_client = boto3_session.client('docdb')
    response = docdb_client.describe_db_clusters(DBClusterIdentifier=db_cluster_identifier)
    return response['DBClusters'][0]['AvailabilityZones']


def delete_instance(boto3_session, db_instance_identifier: str):
    """
    Use delete_db_instance aws method to remove cluster's AvailabilityZones
    :param boto3_session boto3 client session
    :param db_cluster_identifier DocDB cluster ID
    :return Availability Zones of cluster
    """
    docdb_client = boto3_session.client('docdb')
    response = docdb_client.delete_db_instance(DBInstanceIdentifier=db_instance_identifier)
    return response['DBInstance']['DBInstanceIdentifier']
