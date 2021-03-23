import boto3
import random


def get_cluster_az(events, context):
    try:
        docdb = boto3.client('docdb')
        response = docdb.describe_db_clusters(DBClusterIdentifier=events['DBClusterIdentifier'])
        cluster_azs = response['DBClusters'][0]['AvailabilityZones']
        return {'cluster_azs': cluster_azs}
    except Exception as e:
        print(f'Error: {e}')
        raise


def create_new_instance(events, context):
    try:
        docdb = boto3.client('docdb')
        az = events.get('AvailabilityZone')
        instance_az = az if az else random.choice(events['DBClusterAZs'])
        response = docdb.create_db_instance(
            DBInstanceIdentifier=events['DBInstanceIdentifier'],
            DBInstanceClass=events['DBInstanceClass'],
            Engine=events['Engine'],
            AvailabilityZone=instance_az,
            DBClusterIdentifier=events['DBClusterIdentifier']
        )
        return {'instance_az': response['DBInstance']['AvailabilityZone']}
    except Exception as e:
        print(f'Error: {e}')
        raise


def count_cluster_instances(events, context):
    try:
        print(events['DbClusterInstances'])
        return {'DbClusterInstancesNumber': len(events['DbClusterInstances'])}
    except Exception as e:
        print(f'Error: {e}')
        raise


def verify_db_instance_exist(events, context):
    try:
        docdb = boto3.client('docdb')
        response = docdb.describe_db_instances(
            DBInstanceIdentifier=events['DBInstanceIdentifier'],
            Filters=[
                {
                    'Name': 'db-cluster-id',
                    'Values': [
                        events['DBClusterIdentifier'],
                    ]
                },
            ]
        )
        return {events['DBInstanceIdentifier']: response['DBInstances'][0]['DBInstanceStatus']}

    except Exception as e:
        if "DBInstanceNotFound" in str(e):
            raise Exception(
                f"Cluster instance {events['DBInstanceIdentifier']} is not in cluster {events['DBClusterIdentifier']}")
        else:
            print(f'Error: {e}')
            raise


def verify_cluster_instances(events, context):
    try:
        docdb = boto3.client('docdb')
        response = docdb.describe_db_clusters(DBClusterIdentifier=events['DBClusterIdentifier'])
        current_instances_number = len(response['DBClusters'][0]['DBClusterMembers'])
        before_instances_number = events['BeforeDbClusterInstancesNumber']
        if current_instances_number != before_instances_number:
            return {'DbClusterInstancesNumber': current_instances_number}
        else:
            raise Exception('Current cluster instances number equals previous instances number.')
    except Exception as e:
        print(f'Error: {e}')
        raise
