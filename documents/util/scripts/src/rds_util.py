import boto3
from datetime import datetime, timezone

def restore_to_pit(events, context):
    rds = boto3.client('rds')

    if 'DbInstanceIdentifier' not in events or 'TargetDbInstanceIdentifier' not in events:
        raise KeyError('Requires DbInstanceIdentifier, TargetDbInstanceIdentifier in events')

    db_instances_response = rds.describe_db_instances(DBInstanceIdentifier = events['DbInstanceIdentifier'])

    restorable_time = db_instances_response['DBInstances'][0]['LatestRestorableTime']
    current_time = datetime.now(timezone.utc)
    recovery_point_in_seconds = (current_time - restorable_time).seconds

    rds.restore_db_instance_to_point_in_time(
        SourceDBInstanceIdentifier = events['DbInstanceIdentifier'],
        TargetDBInstanceIdentifier = events['TargetDbInstanceIdentifier'],
        RestoreTime = restorable_time,
        DBSubnetGroupName = db_instances_response['DBInstances'][0]['DBSubnetGroup']['DBSubnetGroupName'],
        MultiAZ = db_instances_response['DBInstances'][0]['MultiAZ'],
        PubliclyAccessible = db_instances_response['DBInstances'][0]['PubliclyAccessible'],
        CopyTagsToSnapshot = db_instances_response['DBInstances'][0]['CopyTagsToSnapshot'],
        VpcSecurityGroupIds = [db_instances_response['DBInstances'][0]['VpcSecurityGroups'][0]['VpcSecurityGroupId']]
    )

    output = {}
    output['RecoveryPoint'] = str(recovery_point_in_seconds)
    return output