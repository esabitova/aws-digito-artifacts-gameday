import logging
from boto3 import Session
from .boto3_client_factory import client
from botocore.exceptions import ClientError


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


def get_db_instance_by_id(db_instance_id: str, session: Session):
    """
    Helper function to fetch RDS instance info
    :param db_instance_id: The RDS instance id
    :param session: The boto3 session
    :return: The instance details
    """
    rds_client = client('rds', session)
    db_instances = rds_client.describe_db_instances(DBInstanceIdentifier=db_instance_id)
    return db_instances['DBInstances'][0]


def delete_db_instance(session: Session, db_instance_id: str, async_mode: bool = False,
                       logger: logging.Logger = logging.getLogger()):
    """
    Function to delete RDS instance by given RDS instance id.
    :param session: The boto3 session.
    :param db_instance_id: The RDS instance id to be deleted.
    :param async_mode: (default False) The mode to delete RDS instance,
    if True operation will be blocked till RDS instance is deleted.
    :param logger: The logger.
    """
    rds_client = client('rds', session)
    try:
        logger.info(f'Deleting RDS instance [{db_instance_id}].')
        rds_client.delete_db_instance(DBInstanceIdentifier=db_instance_id,
                                      SkipFinalSnapshot=True,
                                      DeleteAutomatedBackups=True)
        if not async_mode:
            logger.info(f'Waiting for RDS instance [{db_instance_id}] to be deleted.')
            waiter = rds_client.get_waiter('db_instance_deleted')
            waiter.wait(DBInstanceIdentifier=db_instance_id)
    except ClientError as e:
        error_received = e.response['Error']
        error_code_received = error_received.get('Code')
        if error_code_received == 'DBInstanceNotFound':
            logger.warning(f'RDS instance was not deleted due to instance with id [{db_instance_id}] was not found.')
    except Exception:
        raise


def create_db_snapshot(session: Session, db_instance_id: str, snapshot_name: str,
                       async_mode: bool = False, logger: logging.Logger = logging.getLogger()):
    """
    Creates RDS instance snapshot for given instance id and snapshot name.
    :param session: The boto3 session.
    :param db_instance_id: The RDS instance id.
    :param snapshot_name: The snapshot name.
    :param async_mode: async_mode: (default False) The mode to create RDS snapshot,
    if True operation will be blocked till RDS snapshot be in state available.
    :param logger: The logger.
    """
    rds_client = client('rds', session)
    logger.info(f'Creating snapshot [{snapshot_name}] for db instance [{db_instance_id}]')
    rds_client.create_db_snapshot(DBSnapshotIdentifier=snapshot_name,
                                  DBInstanceIdentifier=db_instance_id)
    if not async_mode:
        logger.info(f'Waiting snapshot [{snapshot_name}] for db instance '
                    f'[{db_instance_id}] to be in state [available]')
        waiter = rds_client.get_waiter('db_snapshot_available')
        waiter.wait(DBInstanceIdentifier=db_instance_id,
                    DBSnapshotIdentifier=snapshot_name)
