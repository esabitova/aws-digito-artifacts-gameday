from boto3 import Session
from .boto3_client_factory import client


def get_reader_writer(db_cluster_id: str, session: Session):
    # TODO(semiond): Fix RDS cluster instance retrieval helper function to
    #  fetch all instances available in cluster:
    #  https://issues.amazon.com/issues/Digito-1528
    """
    Helper function to fetch RDS cluster reader/writer
    instance IDs for given RDS cluster id.
    :param db_cluster_id: The RDS cluster id
    :param session: The boto3 session
    :return: The tuple of reader/writer instance IDs
    """
    rds_client = client('rds', session)
    db_cluster_state = rds_client.describe_db_clusters(DBClusterIdentifier=db_cluster_id)
    db_instances = db_cluster_state['DBClusters'][0]['DBClusterMembers']

    for db_instance in db_instances:
        if db_instance['IsClusterWriter']:
            db_writer = db_instance['DBInstanceIdentifier']
        else:
            db_reader = db_instance['DBInstanceIdentifier']
    return (db_reader, db_writer)
