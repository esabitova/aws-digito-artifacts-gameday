def get_number_of_clusters(boto3_session, db_cluster_identifier: str):
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
