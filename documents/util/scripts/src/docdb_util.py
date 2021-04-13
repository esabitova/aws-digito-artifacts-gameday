import random
import boto3
from datetime import datetime
from operator import itemgetter
from botocore.config import Config


def get_cluster_az(events, context):
    try:
        config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
        docdb = boto3.client('docdb', config=config)
        response = docdb.describe_db_clusters(DBClusterIdentifier=events['DBClusterIdentifier'])
        cluster_azs = response['DBClusters'][0]['AvailabilityZones']
        return {'cluster_azs': cluster_azs}
    except Exception as e:
        print(f'Error: {e}')
        raise


def create_new_instance(events, context):
    try:
        config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
        docdb = boto3.client('docdb', config=config)
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
        config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
        docdb = boto3.client('docdb', config=config)
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
        config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
        docdb = boto3.client('docdb', config=config)
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
            config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
            docdb = boto3.client('docdb', config=config)
            response = docdb.describe_db_clusters(DBClusterIdentifier=restorable_cluster_identifier)
            print(response['DBClusters'][0]['LatestRestorableTime'].strftime("%Y-%m-%dT%H:%M:%S%Z"))
            return {'RecoveryPoint': response['DBClusters'][0]['LatestRestorableTime'].strftime("%Y-%d-%mT%H:%M:%S%Z")}
        else:
            return {'RecoveryPoint': date}
    except Exception as e:
        print(f'Error: {e}')
        raise


def restore_to_point_in_time(events, context):
    try:
        config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
        docdb = boto3.client('docdb', config=config)
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
        raise


def restore_db_cluster_instances(events, context):
    try:
        config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
        docdb = boto3.client('docdb', config=config)
        print(events['BackupDbClusterInstancesCountValue'])
        instances = events['BackupDbClusterInstancesCountValue']
        instances_sorted = sorted(instances, key=itemgetter('IsClusterWriter'), reverse=True)
        db_cluster_identifier = events['DBClusterIdentifier']
        restored_instances_identifiers = []
        cluster_info = docdb.describe_db_clusters(DBClusterIdentifier=db_cluster_identifier)['DBClusters'][0]
        new_cluster_azs = cluster_info['AvailabilityZones']
        instances_by_az = {}
        for az in new_cluster_azs:
            instances_by_az[az] = 0
        for instance in instances_sorted:
            primary_instance = 1 if instance['IsClusterWriter'] else 2
            restorable_instance_identifier = instance['DBInstanceIdentifier']
            restored_instance_identifier = instance['DBInstanceIdentifier'] + '-restored'
            availability_zone = None
            if events['DBClusterInstancesMetadata'][restorable_instance_identifier]['AvailabilityZone'] \
                    in new_cluster_azs:
                availability_zone = events['DBClusterInstancesMetadata'][restorable_instance_identifier][
                    'AvailabilityZone']
            else:
                availability_zone = sorted(instances_by_az, key=instances_by_az.get)[0]
            instances_by_az[availability_zone] += 1
            docdb.create_db_instance(
                DBInstanceIdentifier=restored_instance_identifier,
                DBInstanceClass=events['DBClusterInstancesMetadata'][restorable_instance_identifier]['DBInstanceClass'],
                Engine=events['DBClusterInstancesMetadata'][restorable_instance_identifier]['Engine'],
                DBClusterIdentifier=db_cluster_identifier,
                AvailabilityZone=availability_zone,
                PromotionTier=primary_instance
            )
            restored_instances_identifiers.append(restored_instance_identifier)
        return restored_instances_identifiers
    except Exception as e:
        print(f'Error: {e}')
        raise


def rename_restored_db_instances(events, context):
    try:
        config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
        docdb = boto3.client('docdb', config=config)
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
        raise


def backup_cluster_instances_type(events, context):
    try:
        config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
        docdb = boto3.client('docdb', config=config)
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
        raise


def get_latest_snapshot_id(events, context):
    try:
        config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
        docdb = boto3.client('docdb', config=config)
        paginator = docdb.get_paginator('describe_db_cluster_snapshots')
        page_iterator = paginator.paginate(
            DBClusterIdentifier=events['DBClusterIdentifier']
        )
        filtered_iterator = page_iterator.search("sort_by(DBClusterSnapshots, &to_string(SnapshotCreateTime))[-1]")
        latest_snapshot = None
        for snapshot in filtered_iterator:
            latest_snapshot = snapshot
        if latest_snapshot:
            return {
                'LatestSnapshotIdentifier': latest_snapshot['DBClusterSnapshotIdentifier'],
                'LatestSnapshotEngine': latest_snapshot['Engine'],
                'LatestClusterIdentifier': latest_snapshot['DBClusterIdentifier']
            }
        else:
            raise Exception(
                f"No snapshots found for cluster {events['DBClusterIdentifier']}")
    except Exception as e:
        print(f'Error: {e}')
        raise


def restore_db_cluster(events, context):
    try:
        config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
        docdb = boto3.client('docdb', config=config)
        restored_cluster_identifier = events['DBClusterIdentifier'] + '-restored-from-backup'
        if events['DBSnapshotIdentifier'] == '' or events['DBSnapshotIdentifier'] == 'latest':
            docdb.restore_db_cluster_from_snapshot(
                DBClusterIdentifier=restored_cluster_identifier,
                SnapshotIdentifier=events['LatestSnapshotIdentifier'],
                Engine=events['LatestSnapshotEngine']
            )
        else:
            docdb.restore_db_cluster_from_snapshot(
                DBClusterIdentifier=restored_cluster_identifier,
                SnapshotIdentifier=events['DBSnapshotIdentifier'],
                Engine=events['LatestSnapshotEngine']
            )
        return {'RestoredClusterIdentifier': restored_cluster_identifier}
    except Exception as e:
        print(f'Error: {e}')
        raise


def rename_replaced_db_cluster(events, context):
    try:
        config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
        docdb = boto3.client('docdb', config=config)
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
        raise


def rename_replaced_db_instances(events, context):
    try:
        config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
        docdb = boto3.client('docdb', config=config)
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
        raise
