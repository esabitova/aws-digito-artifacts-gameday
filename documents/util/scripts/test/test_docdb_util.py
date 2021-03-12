import unittest
import pytest
from unittest.mock import patch, MagicMock, call
from documents.util.scripts.src.docdb_util import count_cluster_instances, verify_db_instance_exist, \
    verify_cluster_instances

DOCDB_AZ = 'docdb-az'
DOCDB_CLUSTER_ID = 'docdb-cluster-id'
DOCDB_INSTANCE_ID = 'docdb-instance-id'
DOCDB_INSTANCE_STATUS = 'docdb-instance-status'


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
            'DBClusterIdentifier': DOCDB_CLUSTER_ID,
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
    def test_verify_cluster_instances_down(self):
        events = {
            'DBClusterIdentifier': DOCDB_CLUSTER_ID,
            'BeforeDbClusterInstancesNumber': 3
        }

        self.mock_docdb.describe_db_clusters.side_effect = [
            get_docdb_clusters_side_effect(3), get_docdb_clusters_side_effect(3), get_docdb_clusters_side_effect(2)
        ]
        response = verify_cluster_instances(events, None)
        self.mock_docdb.describe_db_clusters.assert_has_calls([
            call(DBClusterIdentifier=DOCDB_CLUSTER_ID),
            call(DBClusterIdentifier=DOCDB_CLUSTER_ID),
            call(DBClusterIdentifier=DOCDB_CLUSTER_ID),
        ])
        self.assertEqual(2, response['DbClusterInstancesNumber'])

    def test_verify_cluster_instances_up(self):
        events = {
            'DBClusterIdentifier': DOCDB_CLUSTER_ID,
            'BeforeDbClusterInstancesNumber': 2
        }

        self.mock_docdb.describe_db_clusters.side_effect = [
            get_docdb_clusters_side_effect(2), get_docdb_clusters_side_effect(2), get_docdb_clusters_side_effect(3)
        ]
        response = verify_cluster_instances(events, None)
        self.mock_docdb.describe_db_clusters.assert_has_calls([
            call(DBClusterIdentifier=DOCDB_CLUSTER_ID),
            call(DBClusterIdentifier=DOCDB_CLUSTER_ID),
            call(DBClusterIdentifier=DOCDB_CLUSTER_ID),
        ])
        self.assertEqual(3, response['DbClusterInstancesNumber'])
