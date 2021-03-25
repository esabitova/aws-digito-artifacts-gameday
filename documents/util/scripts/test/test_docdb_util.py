import unittest
import pytest
from unittest.mock import patch, MagicMock
from documents.util.scripts.src.docdb_util import count_cluster_instances, verify_db_instance_exist, \
    verify_cluster_instances, get_cluster_az, create_new_instance

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


def get_create_db_instance_side_effect(az):
    result = {
        'DBInstance': {
            'AvailabilityZone': az
        }
    }
    return result


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
