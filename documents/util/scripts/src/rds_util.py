import boto3
from datetime import datetime, timezone
from time import sleep
from botocore.config import Config



def restore_to_pit(events, context):
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    rds = boto3.client('rds', config=config)

    if 'DbInstanceIdentifier' not in events or 'TargetDbInstanceIdentifier' not in events:
        raise KeyError('Requires DbInstanceIdentifier, TargetDbInstanceIdentifier in events')

    db_instances_response = rds.describe_db_instances(DBInstanceIdentifier=events['DbInstanceIdentifier'])

    restorable_time = db_instances_response['DBInstances'][0]['LatestRestorableTime']
    current_time = datetime.now(timezone.utc)
    recovery_point_in_seconds = (current_time - restorable_time).seconds

    rds.restore_db_instance_to_point_in_time(
        SourceDBInstanceIdentifier=events['DbInstanceIdentifier'],
        TargetDBInstanceIdentifier=events['TargetDbInstanceIdentifier'],
        RestoreTime=restorable_time,
        DBSubnetGroupName=db_instances_response['DBInstances'][0]['DBSubnetGroup']['DBSubnetGroupName'],
        MultiAZ=db_instances_response['DBInstances'][0]['MultiAZ'],
        PubliclyAccessible=db_instances_response['DBInstances'][0]['PubliclyAccessible'],
        CopyTagsToSnapshot=db_instances_response['DBInstances'][0]['CopyTagsToSnapshot'],
        VpcSecurityGroupIds=[db_instances_response['DBInstances'][0]['VpcSecurityGroups'][0]['VpcSecurityGroupId']]
    )

    output = {}
    output['RecoveryPoint'] = str(recovery_point_in_seconds)
    return output


def get_cluster_writer_id(events, context):
    if 'ClusterId' not in events:
        raise KeyError('Requires ClusterId in events')
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    rds = boto3.client('rds', config=config)
    clusters = rds.describe_db_clusters(DBClusterIdentifier=events['ClusterId'])
    return {'WriterId': _parse_writer_id(clusters)}


def wait_cluster_failover_completed(events, context):
    '''
    Failover times are typically 60–120 seconds, should not be a problem for lambda
    (Lambda is used for execution SSM scripts):
    https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.MultiAZ.html
    '''
    if 'ClusterId' not in events or 'WriterId' not in events:
        raise KeyError('Requires ClusterId, WriterId in events')
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    rds = boto3.client('rds', config=config)
    clusters = rds.describe_db_clusters(DBClusterIdentifier=events['ClusterId'])
    current_writer_id = _parse_writer_id(clusters)
    status = clusters['DBClusters'][0]['Status']
    while current_writer_id == events['WriterId'] or status != 'available':
        sleep(5)
        clusters = rds.describe_db_clusters(DBClusterIdentifier=events['ClusterId'])
        current_writer_id = _parse_writer_id(clusters)
        status = clusters['DBClusters'][0]['Status']


def _parse_writer_id(clusters):
    for member in clusters['DBClusters'][0]['DBClusterMembers']:
        if member['IsClusterWriter'] is True:
            return member['DBInstanceIdentifier']
