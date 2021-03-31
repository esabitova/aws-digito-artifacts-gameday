import boto3
import random
from datetime import datetime
from operator import itemgetter


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


def get_recovery_point_input(events, context):
    try:
        date = events['RestoreToDate']
        restorable_cluster_identifier = events['DBClusterIdentifier']
        if date == 'latest':
            docdb = boto3.client('docdb')
            response = docdb.describe_db_clusters(DBClusterIdentifier=restorable_cluster_identifier)
            print(response['DBClusters'][0]['LatestRestorableTime'].strftime("%Y-%m-%dT%H:%M:%S%Z"))
            return {'RecoveryPoint': response['DBClusters'][0]['LatestRestorableTime'].strftime("%Y-%d-%mT%H:%M:%S%Z")}
        else:
            return {'RecoveryPoint': date}
    except Exception as e:
        print(f'Error: {e}')


def backup_cluster_instances_type(events, context):
    try:
        docdb = boto3.client('docdb')
        restorable_instances_metadata = {}
        instance_type = {}
        instances = events['DBClusterInstances']
        for instance in instances:
            response = docdb.describe_db_instances(DBInstanceIdentifier=instance['DBInstanceIdentifier'])
            print(response)
            instance_id = instance['DBInstanceIdentifier']
            instance_type[instance_id] = {
                'DBInstanceClass': response['DBInstances'][0]['DBInstanceClass'],
                'Engine': response['DBInstances'][0]['Engine'],
                'AvailabilityZone': response['DBInstances'][0]['AvailabilityZone']
            }
            restorable_instances_metadata.update(instance_type)
        return {'DBClusterInstancesMetadata': restorable_instances_metadata}
    except Exception as e:
        print(f'Error: {e}')


def restore_to_point_in_time(events, context):
    try:
        docdb = boto3.client('docdb')
        restorable_cluster_identifier = events['DBClusterIdentifier']
        new_cluster_identifier = restorable_cluster_identifier + '-restored'
        date = events['RestoreToDate']
        security_groups = events['VpcSecurityGroupIds']
        if date == 'latest':
            docdb.restore_db_cluster_to_point_in_time(
                DBClusterIdentifier=new_cluster_identifier,
                SourceDBClusterIdentifier=restorable_cluster_identifier,
                UseLatestRestorableTime=True,
                VpcSecurityGroupIds=security_groups
            )
        else:
            date = datetime.strptime(events['RestoreToDate'], "%Y-%m-%dT%H:%M:%S%z")
            print(date)
            docdb.restore_db_cluster_to_point_in_time(
                DBClusterIdentifier=new_cluster_identifier,
                SourceDBClusterIdentifier=restorable_cluster_identifier,
                RestoreToTime=date,
                VpcSecurityGroupIds=security_groups
            )
        return {'RestoredClusterIdentifier': new_cluster_identifier}
    except Exception as e:
        print(f'Error: {e}')


def restore_db_cluster_instances(events, context):
    try:
        docdb = boto3.client('docdb')
        print(events['BackupDbClusterInstancesCountValue'])
        instances = events['BackupDbClusterInstancesCountValue']
        instances_sorted = sorted(instances, key=itemgetter('IsClusterWriter'), reverse=True)
        db_cluster_identifier = events['DBClusterIdentifier']
        restored_instances_identifiers = []
        for instance in instances_sorted:
            primary_instance = 1 if instance['IsClusterWriter'] else 2
            restorable_instance_identifier = instance['DBInstanceIdentifier']
            restored_instance_identifier = instance['DBInstanceIdentifier'] + '-restored'
            docdb.create_db_instance(
                DBInstanceIdentifier=restored_instance_identifier,
                DBInstanceClass=events['DBClusterInstancesMetadata'][restorable_instance_identifier]['DBInstanceClass'],
                Engine=events['DBClusterInstancesMetadata'][restorable_instance_identifier]['Engine'],
                DBClusterIdentifier=db_cluster_identifier,
                AvailabilityZone=events['DBClusterInstancesMetadata'][restorable_instance_identifier][
                    'AvailabilityZone'],
                PromotionTier=primary_instance
            )
            restored_instances_identifiers.append(restored_instance_identifier)
        return restored_instances_identifiers
    except Exception as e:
        print(f'Error: {e}')


def rename_replaced_db_cluster(events, context):
    try:
        docdb = boto3.client('docdb')
        db_cluster_identifier = events['DBClusterIdentifier']
        new_db_cluster_identifier = db_cluster_identifier + '-replaced'
        docdb.modify_db_cluster(
            DBClusterIdentifier=db_cluster_identifier,
            NewDBClusterIdentifier=new_db_cluster_identifier,
            ApplyImmediately=True,
        )
        return {'ReplacedClusterIdentifier': new_db_cluster_identifier}
    except Exception as e:
        print(f'Error: {e}')


def rename_replaced_db_instances(events, context):
    try:
        docdb = boto3.client('docdb')
        instances = events['BackupDbClusterInstancesCountValue']
        replaced_instances_identifiers = []
        for instance in instances:
            docdb.modify_db_instance(
                DBInstanceIdentifier=instance['DBInstanceIdentifier'],
                ApplyImmediately=True,
                NewDBInstanceIdentifier=instance['DBInstanceIdentifier'] + '-replaced',
            )
            replaced_instances_identifiers.append(instance['DBInstanceIdentifier'] + '-replaced')
        return replaced_instances_identifiers
    except Exception as e:
        print(f'Error: {e}')


def rename_restored_db_instances(events, context):
    try:
        docdb = boto3.client('docdb')
        instances = events['RestoredInstancesIdentifiers']
        restored_instances_identifiers = []
        for instance in instances:
            restored_instance_identifier = instance.replace('-restored', '')
            docdb.modify_db_instance(
                DBInstanceIdentifier=instance,
                ApplyImmediately=True,
                NewDBInstanceIdentifier=restored_instance_identifier
            )
            restored_instances_identifiers.append(restored_instance_identifier)
        return restored_instances_identifiers
    except Exception as e:
        print(f'Error: {e}')
