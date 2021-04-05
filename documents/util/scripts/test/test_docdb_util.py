import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock, call

import pytest

from documents.util.scripts.src.docdb_util import count_cluster_instances, verify_db_instance_exist, \
    verify_cluster_instances, get_cluster_az, create_new_instance, get_recovery_point_input, \
    backup_cluster_instances_type, restore_to_point_in_time, restore_db_cluster_instances, rename_replaced_db_cluster, \
    rename_replaced_db_instances, rename_restored_db_instances

DOCDB_AZ = 'docdb-az'
DOCDB_CLUSTER_ID = 'docdb-cluster-id'
DOCDB_INSTANCE_ID = 'docdb-instance-id'
DOCDB_INSTANCE_STATUS = 'docdb-instance-status'
DOCDB_ENGINE = 'docdb'
DOCDB_INSTANCE_CLASS = 'db.r5.large'


def get_docdb_clusters_side_effect(number_of_instances=1):
    result = {
        'DBClusters': [
            {
                'AvailabilityZones': [DOCDB_AZ],
                'DBClusterIdentifier': DOCDB_CLUSTER_ID,
                'DBClusterMembers': []
            }
        ]
    }
    is_first = True
    for i in range(0, number_of_instances):
        instance = {'DBInstanceIdentifier': DOCDB_INSTANCE_ID + f'-{i}', 'IsClusterWriter': is_first}
        result['DBClusters'][0]['DBClusterMembers'].append(instance)
        is_first = False
    return result


def get_docdb_instances_with_status_side_effect(number_of_instances):
    result = {
        'DBInstances': []
    }
    for i in range(0, number_of_instances):
        result['DBInstances'].append({
            'DBInstanceStatus': 'available'
        })
    return result


def get_docdb_clusters_restore_date_side_effect(date):
    return {
        'DBClusters': [
            {'LatestRestorableTime': date}
        ]
    }


def get_create_db_instance_side_effect(az):
    result = {
        'DBInstance': {
            'AvailabilityZone': az
        }
    }
    return result


def get_docdb_instances_side_effect(az):
    return {'DBInstances': [{'AvailabilityZone': az}]}


def get_cluster_azs_side_effect():
    return {'DBClusters': [{'AvailabilityZones': ['us-east-1a', 'us-east-1b', 'us-east-1c']}]}


DOCDB_INSTANCES = {
    'DBInstances': [
        {
            'DBInstanceStatus': DOCDB_INSTANCE_STATUS
        }
    ]
}


@pytest.mark.unit_test
class TestDocDBUtil(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('boto3.client')
        self.client = self.patcher.start()
        self.mock_docdb = MagicMock()
        self.side_effect_map = {
            'docdb': self.mock_docdb
        }
        self.client.side_effect = lambda service_name: self.side_effect_map.get(service_name)

        self.mock_docdb.describe_db_instances.return_value = DOCDB_INSTANCES

    def tearDown(self):
        self.patcher.stop()

    # Test count_cluster_instances
    def test_count_cluster_instances(self):
        events = {
            'DbClusterInstances': get_docdb_clusters_side_effect(3)['DBClusters'][0]['DBClusterMembers']
        }
        response = count_cluster_instances(events, None)
        self.assertEqual(3, response['DbClusterInstancesNumber'])

    def test_count_cluster_instances_empty(self):
        events = {
            'DbClusterInstances': []
        }
        response = count_cluster_instances(events, None)
        self.assertEqual(0, response['DbClusterInstancesNumber'])

    def test_count_cluster_instances_missing(self):
        events = {}
        self.assertRaises(Exception, count_cluster_instances, events, None)

    # Test verify_db_instance_exist

    def test_verify_db_instance_exist(self):
        events = {
            'DBInstanceIdentifier': DOCDB_INSTANCE_ID,
            'DBClusterIdentifier': DOCDB_CLUSTER_ID,
        }
        response = verify_db_instance_exist(events, None)
        self.mock_docdb.describe_db_instances.assert_called_once_with(
            DBInstanceIdentifier=DOCDB_INSTANCE_ID,
            Filters=[
                {
                    'Name': 'db-cluster-id',
                    'Values': [DOCDB_CLUSTER_ID]
                },
            ]
        )
        self.assertEqual(DOCDB_INSTANCE_STATUS, response[DOCDB_INSTANCE_ID])

    def test_verify_db_instance_exist_missing_instance_id(self):
        events = {
            'DBClusterIdentifier': DOCDB_CLUSTER_ID,
        }
        self.assertRaises(Exception, verify_db_instance_exist, events, None)

    def test_verify_db_instance_exist_missing_cluster_id(self):
        events = {
            'DBInstanceIdentifier': DOCDB_INSTANCE_ID,
        }
        self.assertRaises(Exception, verify_db_instance_exist, events, None)

    def test_verify_db_instance_exist_not_found(self):
        events = {
            'DBInstanceIdentifier': DOCDB_INSTANCE_ID,
            'DBClusterIdentifier': DOCDB_CLUSTER_ID,
        }
        self.mock_docdb.describe_db_instances.side_effect = MagicMock(side_effect=Exception('DBInstanceNotFound'))
        self.assertRaises(Exception, verify_db_instance_exist, events, None)
        self.mock_docdb.describe_db_instances.assert_called_once_with(
            DBInstanceIdentifier=DOCDB_INSTANCE_ID,
            Filters=[
                {
                    'Name': 'db-cluster-id',
                    'Values': [DOCDB_CLUSTER_ID]
                },
            ]
        )

    # Test verify_cluster_instances

    def test_verify_cluster_instances(self):
        events = {
            'DBClusterIdentifier': DOCDB_CLUSTER_ID,
            'BeforeDbClusterInstancesNumber': 2
        }

        self.mock_docdb.describe_db_clusters.return_value = get_docdb_clusters_side_effect(3)
        response = verify_cluster_instances(events, None)
        self.mock_docdb.describe_db_clusters.assert_called_once_with(DBClusterIdentifier=DOCDB_CLUSTER_ID)
        self.assertEqual(3, response['DbClusterInstancesNumber'])

    def test_verify_cluster_instances_not_changed(self):
        events = {
            'DBClusterIdentifier': DOCDB_CLUSTER_ID,
            'BeforeDbClusterInstancesNumber': 3
        }

        self.mock_docdb.describe_db_clusters.return_value = get_docdb_clusters_side_effect(3)
        self.assertRaises(Exception, verify_cluster_instances, events, None)
        self.mock_docdb.describe_db_clusters.assert_called_once_with(DBClusterIdentifier=DOCDB_CLUSTER_ID)

    def test_verify_cluster_instances_missing_id(self):
        events = {}
        self.assertRaises(Exception, verify_cluster_instances, events, None)

    def test_verify_cluster_instances_missing_old_value(self):
        events = {
            'DBClusterIdentifier': DOCDB_CLUSTER_ID
        }
        self.assertRaises(Exception, verify_cluster_instances, events, None)

    # Test get_cluster_az
    def test_get_cluster_az_empty_events(self):
        events = {}
        self.assertRaises(Exception, get_cluster_az, events, None)

    def test_get_cluster_az_valid_cluster(self):
        events = {
            'DBClusterIdentifier': DOCDB_CLUSTER_ID
        }
        self.mock_docdb.describe_db_clusters.return_value = get_docdb_clusters_side_effect(1)
        response = get_cluster_az(events, None)
        self.assertEqual([DOCDB_AZ], response['cluster_azs'])

    def test_get_cluster_az_not_existing_cluster(self):
        events = {
            'DBClusterIdentifier': 'NOT_EXISTING_CLUSTER_ID'
        }
        self.mock_docdb.describe_db_clusters.return_value = {}
        self.assertRaises(Exception, get_cluster_az, events, None)

    # Test create_new_instance
    def test_create_new_instance_az_from_AvailabilityZone(self):
        events = {
            'AvailabilityZone': DOCDB_AZ,
            'DBInstanceIdentifier': 'id1',
            'DBInstanceClass': DOCDB_INSTANCE_CLASS,
            'Engine': DOCDB_ENGINE,
            'DBClusterIdentifier': DOCDB_CLUSTER_ID
        }
        self.mock_docdb.create_db_instance.return_value = get_create_db_instance_side_effect(DOCDB_AZ)
        response = create_new_instance(events, None)
        self.assertEqual({'instance_az': DOCDB_AZ}, response)
        self.mock_docdb.create_db_instance.assert_called_once_with(
            AvailabilityZone=DOCDB_AZ,
            DBInstanceIdentifier='id1',
            DBInstanceClass=DOCDB_INSTANCE_CLASS,
            Engine=DOCDB_ENGINE,
            DBClusterIdentifier=DOCDB_CLUSTER_ID
        )

    def test_create_new_instance_az_from_DBClusterAZs(self):
        events = {
            'DBClusterAZs': [DOCDB_AZ],
            'DBInstanceIdentifier': 'id1',
            'DBInstanceClass': DOCDB_INSTANCE_CLASS,
            'Engine': DOCDB_ENGINE,
            'DBClusterIdentifier': DOCDB_CLUSTER_ID
        }
        self.mock_docdb.create_db_instance.return_value = get_create_db_instance_side_effect(DOCDB_AZ)
        response = create_new_instance(events, None)
        self.assertEqual({'instance_az': DOCDB_AZ}, response)
        self.mock_docdb.create_db_instance.assert_called_once_with(
            AvailabilityZone=DOCDB_AZ,
            DBInstanceIdentifier='id1',
            DBInstanceClass=DOCDB_INSTANCE_CLASS,
            Engine=DOCDB_ENGINE,
            DBClusterIdentifier=DOCDB_CLUSTER_ID
        )

    def test_create_new_instance_missing_az(self):
        events = {
            'DBInstanceIdentifier': 'id1',
            'DBInstanceClass': DOCDB_INSTANCE_CLASS,
            'Engine': DOCDB_ENGINE,
            'DBClusterIdentifier': DOCDB_CLUSTER_ID
        }
        self.mock_docdb.create_db_instance.return_value = get_create_db_instance_side_effect(DOCDB_AZ)
        self.assertRaises(Exception, create_new_instance, events, None)

    def test_create_new_instance_missing_instance_identifier(self):
        events = {
            'DBClusterAZs': [DOCDB_AZ],
            'DBInstanceClass': DOCDB_INSTANCE_CLASS,
            'Engine': DOCDB_ENGINE,
            'DBClusterIdentifier': DOCDB_CLUSTER_ID
        }
        self.mock_docdb.create_db_instance.return_value = get_create_db_instance_side_effect(DOCDB_AZ)
        self.assertRaises(Exception, create_new_instance, events, None)

    def test_create_new_instance_missing_cluster_identifier(self):
        events = {
            'DBClusterAZs': [DOCDB_AZ],
            'DBInstanceIdentifier': 'id1',
            'DBInstanceClass': DOCDB_INSTANCE_CLASS,
            'Engine': DOCDB_ENGINE,
        }
        self.mock_docdb.create_db_instance.return_value = get_create_db_instance_side_effect(DOCDB_AZ)
        self.assertRaises(Exception, create_new_instance, events, None)

    def test_create_new_instance_missing_engine(self):
        events = {
            'DBClusterAZs': [DOCDB_AZ],
            'DBInstanceIdentifier': 'id1',
            'DBInstanceClass': DOCDB_INSTANCE_CLASS,
            'DBClusterIdentifier': DOCDB_CLUSTER_ID
        }
        self.mock_docdb.create_db_instance.return_value = get_create_db_instance_side_effect(DOCDB_AZ)
        self.assertRaises(Exception, create_new_instance, events, None)

    def test_create_new_instance_missing_instance_class(self):
        events = {
            'DBClusterAZs': [DOCDB_AZ],
            'DBInstanceIdentifier': 'id1',
            'Engine': DOCDB_ENGINE,
            'DBClusterIdentifier': DOCDB_CLUSTER_ID
        }
        self.mock_docdb.create_db_instance.return_value = get_create_db_instance_side_effect(DOCDB_AZ)
        self.assertRaises(Exception, create_new_instance, events, None)

    # Test get_recovery_time_input
    def test_get_recovery_time_input_latest_date(self):
        events = {
            'RestoreToDate': 'latest',
            'DBClusterIdentifier': DOCDB_CLUSTER_ID
        }
        date = datetime(2020, 1, 1, 0, 0)
        self.mock_docdb.describe_db_clusters.return_value = get_docdb_clusters_restore_date_side_effect(date)
        response = get_recovery_point_input(events, None)
        self.assertEqual({'RecoveryPoint': '2020-01-01T00:00:00'}, response)
        self.mock_docdb.describe_db_clusters.assert_called_once_with(
            DBClusterIdentifier=DOCDB_CLUSTER_ID
        )

    def test_get_recovery_time_input_actual_date(self):
        events = {
            'RestoreToDate': '2020-01-01T00:00:00',
            'DBClusterIdentifier': DOCDB_CLUSTER_ID
        }
        self.mock_docdb.describe_db_clusters.return_value = get_docdb_clusters_restore_date_side_effect('')
        response = get_recovery_point_input(events, None)
        self.assertEqual({'RecoveryPoint': '2020-01-01T00:00:00'}, response)

    def test_get_recovery_time_input_missing_restore_to_date(self):
        events = {
            'DBClusterIdentifier': DOCDB_CLUSTER_ID
        }
        self.assertRaises(Exception, get_recovery_point_input, events, None)

    def test_get_recovery_time_input_missing_db_cluster_identifier(self):
        events = {
            'RestoreToDate': '2020-01-01T00:00:00',
        }
        self.assertRaises(Exception, get_recovery_point_input, events, None)

    # Test backup_cluster_instances_type
    def test_backup_cluster_instances_type(self):
        cluster_members = [{
            'DBInstanceIdentifier': 'Instance1',
            'IsClusterWriter': True
        }, {
            'DBInstanceIdentifier': 'Instance2',
            'IsClusterWriter': False
        }]
        events = {'DBClusterInstances': cluster_members}
        self.mock_docdb.describe_db_instances.side_effect = [
            {'DBInstances': [
                {
                    'DBInstanceIdentifier': 'Instance1',
                    'DBInstanceClass': DOCDB_INSTANCE_CLASS,
                    'Engine': DOCDB_ENGINE,
                    'AvailabilityZone': DOCDB_AZ
                }
            ]},
            {'DBInstances': [
                {
                    'DBInstanceIdentifier': 'Instance2',
                    'DBInstanceClass': DOCDB_INSTANCE_CLASS,
                    'Engine': DOCDB_ENGINE,
                    'AvailabilityZone': DOCDB_AZ
                }
            ]}
        ]

        response = backup_cluster_instances_type(events, None)
        self.assertEqual({
            'DBClusterInstancesMetadata': {
                'Instance1': {
                    'DBInstanceClass': DOCDB_INSTANCE_CLASS,
                    'Engine': DOCDB_ENGINE,
                    'AvailabilityZone': DOCDB_AZ
                },
                'Instance2': {
                    'DBInstanceClass': DOCDB_INSTANCE_CLASS,
                    'Engine': DOCDB_ENGINE,
                    'AvailabilityZone': DOCDB_AZ
                }}
        }, response)
        calls = [
            call(DBInstanceIdentifier='Instance1'),
            call(DBInstanceIdentifier='Instance2')
        ]
        self.mock_docdb.describe_db_instances.assert_has_calls(calls)

    def test_backup_cluster_instances_type_empty_events(self):
        events = {}
        self.assertRaises(Exception, backup_cluster_instances_type, events, None)

    # Test restore_to_point_in_time
    def test_restore_to_point_in_time_restore_date_latest(self):
        vpc_security_group_ids = ['vpc1', 'vpc2']
        events = {
            'DBClusterIdentifier': DOCDB_CLUSTER_ID,
            'RestoreToDate': 'latest',
            'VpcSecurityGroupIds': vpc_security_group_ids
        }
        response = restore_to_point_in_time(events, None)
        new_cluster_identifier = DOCDB_CLUSTER_ID + '-restored'
        self.mock_docdb.restore_db_cluster_to_point_in_time.assert_called_once_with(
            DBClusterIdentifier=new_cluster_identifier,
            SourceDBClusterIdentifier=DOCDB_CLUSTER_ID,
            UseLatestRestorableTime=True,
            VpcSecurityGroupIds=vpc_security_group_ids
        )
        self.assertEqual({'RestoredClusterIdentifier': new_cluster_identifier}, response)

    def test_restore_to_point_in_time_actual_restore_date(self):
        vpc_security_group_ids = ['vpc1', 'vpc2']
        date = '2020-01-01T00:00:00Z'
        events = {
            'DBClusterIdentifier': DOCDB_CLUSTER_ID,
            'RestoreToDate': date,
            'VpcSecurityGroupIds': vpc_security_group_ids
        }
        response = restore_to_point_in_time(events, None)
        new_cluster_identifier = DOCDB_CLUSTER_ID + '-restored'
        self.mock_docdb.restore_db_cluster_to_point_in_time.assert_called_once_with(
            DBClusterIdentifier=new_cluster_identifier,
            SourceDBClusterIdentifier=DOCDB_CLUSTER_ID,
            RestoreToTime=datetime.strptime(date, "%Y-%m-%dT%H:%M:%S%z"),
            VpcSecurityGroupIds=vpc_security_group_ids
        )
        self.assertEqual({'RestoredClusterIdentifier': new_cluster_identifier}, response)

    def test_restore_to_point_in_time_empty_events(self):
        events = {}
        self.assertRaises(Exception, restore_to_point_in_time, events, None)

    # Test restore_db_cluster_instances
    def test_restore_db_cluster_instances_same_cluster_azs(self):
        events = {
            'BackupDbClusterInstancesCountValue': [
                {
                    'DBInstanceIdentifier': 'Instance1',
                    'IsClusterWriter': True
                }, {
                    'DBInstanceIdentifier': 'Instance2',
                    'IsClusterWriter': False
                }
            ],
            'DBClusterIdentifier': DOCDB_CLUSTER_ID,
            'DBClusterInstancesMetadata': {
                'Instance1': {
                    'DBInstanceClass': DOCDB_INSTANCE_CLASS,
                    'Engine': DOCDB_ENGINE,
                    'AvailabilityZone': 'us-east-1a'
                },
                'Instance2': {
                    'DBInstanceClass': DOCDB_INSTANCE_CLASS,
                    'Engine': DOCDB_ENGINE,
                    'AvailabilityZone': 'us-east-1b'
                }
            }
        }
        self.mock_docdb.describe_db_clusters.return_value = {
            'DBClusters': [
                {
                    'DBClusterIdentifier': DOCDB_CLUSTER_ID,
                    'AvailabilityZones': ['us-east-1a', 'us-east-1b']
                }
            ]
        }
        response = restore_db_cluster_instances(events, None)
        calls = [
            call(
                DBInstanceIdentifier='Instance1-restored',
                DBInstanceClass=DOCDB_INSTANCE_CLASS,
                Engine=DOCDB_ENGINE,
                DBClusterIdentifier=DOCDB_CLUSTER_ID,
                AvailabilityZone='us-east-1a',
                PromotionTier=1
            ),
            call(
                DBInstanceIdentifier='Instance2-restored',
                DBInstanceClass=DOCDB_INSTANCE_CLASS,
                Engine=DOCDB_ENGINE,
                DBClusterIdentifier=DOCDB_CLUSTER_ID,
                AvailabilityZone='us-east-1b',
                PromotionTier=2
            )
        ]
        self.mock_docdb.create_db_instance.assert_has_calls(calls)
        self.assertEqual(['Instance1-restored', 'Instance2-restored'], response)

    def test_restore_db_cluster_instances_different_cluster_azs(self):
        events = {
            'BackupDbClusterInstancesCountValue': [
                {
                    'DBInstanceIdentifier': 'Instance1',
                    'IsClusterWriter': True
                }, {
                    'DBInstanceIdentifier': 'Instance2',
                    'IsClusterWriter': False
                }, {
                    'DBInstanceIdentifier': 'Instance3',
                    'IsClusterWriter': False
                }
            ],
            'DBClusterIdentifier': DOCDB_CLUSTER_ID,
            'DBClusterInstancesMetadata': {
                'Instance1': {
                    'DBInstanceClass': DOCDB_INSTANCE_CLASS,
                    'Engine': DOCDB_ENGINE,
                    'AvailabilityZone': 'us-east-1a'
                },
                'Instance2': {
                    'DBInstanceClass': DOCDB_INSTANCE_CLASS,
                    'Engine': DOCDB_ENGINE,
                    'AvailabilityZone': 'us-east-1b'
                },
                'Instance3': {
                    'DBInstanceClass': DOCDB_INSTANCE_CLASS,
                    'Engine': DOCDB_ENGINE,
                    'AvailabilityZone': 'us-east-1c'
                }
            }
        }
        self.mock_docdb.describe_db_clusters.return_value = {
            'DBClusters': [
                {
                    'DBClusterIdentifier': DOCDB_CLUSTER_ID,
                    'AvailabilityZones': ['us-east-1a', 'us-east-1d', 'us-east-1f']
                }
            ]
        }
        response = restore_db_cluster_instances(events, None)
        calls = [
            call(
                DBInstanceIdentifier='Instance1-restored',
                DBInstanceClass=DOCDB_INSTANCE_CLASS,
                Engine=DOCDB_ENGINE,
                DBClusterIdentifier=DOCDB_CLUSTER_ID,
                AvailabilityZone='us-east-1a',
                PromotionTier=1
            ),
            call(
                DBInstanceIdentifier='Instance2-restored',
                DBInstanceClass=DOCDB_INSTANCE_CLASS,
                Engine=DOCDB_ENGINE,
                DBClusterIdentifier=DOCDB_CLUSTER_ID,
                AvailabilityZone='us-east-1d',
                PromotionTier=2
            ),
            call(
                DBInstanceIdentifier='Instance3-restored',
                DBInstanceClass=DOCDB_INSTANCE_CLASS,
                Engine=DOCDB_ENGINE,
                DBClusterIdentifier=DOCDB_CLUSTER_ID,
                AvailabilityZone='us-east-1f',
                PromotionTier=2
            )
        ]
        self.mock_docdb.create_db_instance.assert_has_calls(calls)
        self.assertEqual(['Instance1-restored', 'Instance2-restored', 'Instance3-restored'], response)

    def test_create_db_instance_empty_events(self):
        self.assertRaises(Exception, restore_db_cluster_instances, {}, None)

    # Test rename_replaced_db_cluster
    def test_rename_replaced_db_cluster(self):
        events = {
            'DBClusterIdentifier': DOCDB_CLUSTER_ID
        }
        response = rename_replaced_db_cluster(events, None)
        self.mock_docdb.modify_db_cluster.assert_called_once_with(
            DBClusterIdentifier=DOCDB_CLUSTER_ID,
            NewDBClusterIdentifier=DOCDB_CLUSTER_ID + '-replaced',
            ApplyImmediately=True
        )
        self.assertEqual({'ReplacedClusterIdentifier': DOCDB_CLUSTER_ID + '-replaced'}, response)

    def test_rename_replaced_db_cluster_empty_events(self):
        self.assertRaises(Exception, rename_replaced_db_cluster, {}, None)

    # Test rename_replaced_db_instances
    def test_rename_replaced_db_instances(self):
        events = {
            'BackupDbClusterInstancesCountValue': [
                {
                    'DBInstanceIdentifier': 'Instance1',
                    'IsClusterWriter': True
                }, {
                    'DBInstanceIdentifier': 'Instance2',
                    'IsClusterWriter': False
                }
            ],
        }
        response = rename_replaced_db_instances(events, None)
        calls = [
            call(
                DBInstanceIdentifier='Instance1',
                ApplyImmediately=True,
                NewDBInstanceIdentifier='Instance1-replaced',
            ),
            call(
                DBInstanceIdentifier='Instance2',
                ApplyImmediately=True,
                NewDBInstanceIdentifier='Instance2-replaced',
            )
        ]
        self.mock_docdb.modify_db_instance.assert_has_calls(calls)
        self.assertEqual(['Instance1-replaced', 'Instance2-replaced'], response)

    def test_rename_replaced_db_instances_empty_events(self):
        self.assertRaises(Exception, rename_replaced_db_instances, {}, None)

    # Test rename_restored_db_instances
    def test_rename_restored_db_instances(self):
        events = {
            'RestoredInstancesIdentifiers': ['Instance1-restored', 'Instance2-restored']
        }
        response = rename_restored_db_instances(events, None)
        calls = [
            call(
                DBInstanceIdentifier='Instance1-restored',
                ApplyImmediately=True,
                NewDBInstanceIdentifier='Instance1'
            ),
            call(
                DBInstanceIdentifier='Instance2-restored',
                ApplyImmediately=True,
                NewDBInstanceIdentifier='Instance2'
            )
        ]
        self.mock_docdb.modify_db_instance.assert_has_calls(calls)
        self.assertEqual(['Instance1', 'Instance2'], response)

    def test_rename_restored_db_instances_empty_events(self):
        self.assertRaises(Exception, rename_restored_db_instances, {}, None)
