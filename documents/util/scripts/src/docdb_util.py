import boto3
import random


def get_cluster_az(events, context):
    try:
        docdb = boto3.client('docdb')
        response = docdb.describe_db_clusters(DBClusterIdentifier=events['DBClusterIdentifier'])
        cluster_az = response['DBClusters'][0]['AvailabilityZones']
        return {'cluster_az': cluster_az}
    except Exception as e:
        print(f'Error: {e}')


def create_new_instance(events, context):
    try:
        docdb = boto3.client('docdb')
        instance_az = events['AvailabilityZone'] if events['AvailabilityZone'] else random.choice(events['DBClusterAZ'])
        docdb.create_db_instance(
            DBInstanceIdentifier=events['DBInstanceIdentifier'],
            DBInstanceClass=events['DBInstanceClass'],
            Engine=events['Engine'],
            AvailabilityZone=instance_az,
            DBClusterIdentifier=events['DBClusterIdentifier']
        )
        return {'instance_az': instance_az}
    except Exception as e:
        print(f'Error: {e}')
