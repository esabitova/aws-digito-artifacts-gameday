def get_number_of_instances(boto3_session, db_cluster_identifier: str):
    """
    Use describe_db_clusters aws method to get a list of DocDB cluster members and return their amount
    :param boto3_session boto3 client session
    :param db_cluster_identifier DocDB cluster ID
    :return Number of DocDB cluster members
    """
    docdb_client = boto3_session.client('docdb')
    response = docdb_client.describe_db_clusters(DBClusterIdentifier=db_cluster_identifier)
    if response['DBClusters'] and response['DBClusters'][0]:
        return len(response['DBClusters'][0]['DBClusterMembers'])
    return 0


def get_instance_az(boto3_session, db_instance_identifier: str):
    """
    Use describe_db_instances aws method to get a Availability Zone of DocDB instance
    :param boto3_session boto3 client session
    :param db_instance_identifier DocDB instance ID
    :return Availability Zone of DocDB instance
    """
    docdb_client = boto3_session.client('docdb')
    response = docdb_client.describe_db_instances(DBInstanceIdentifier=db_instance_identifier)
    print("response")
    print(response)
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
