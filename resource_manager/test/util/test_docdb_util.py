import unittest
from unittest.mock import MagicMock, call, patch

import pytest
from botocore.exceptions import ClientError

import resource_manager.src.util.boto3_client_factory as client_factory
import resource_manager.src.util.docdb_utils as docdb_utils
from documents.util.scripts.test.test_docdb_util import DOCDB_CLUSTER_ID, DOCDB_INSTANCE_ID, DOCDB_SUBNET_GROUP_NAME, \
    get_docdb_instances_side_effect, get_describe_db_cluster_side_effect, \
    get_docdb_instances_with_status_side_effect, get_subnet_group_side_effect
from documents.util.scripts.test.mock_sleep import MockSleep


@pytest.mark.unit_test
class TestDocDBUtil(unittest.TestCase):

    def setUp(self):
        self.session_mock = MagicMock()
        self.mock_docdb_service = MagicMock()
        self.client_side_effect_map = {
            'docdb': self.mock_docdb_service
        }
        self.session_mock.client.side_effect = lambda service_name, config=None: \
            self.client_side_effect_map.get(service_name)

    def tearDown(self):
        # Clean client factory cache after each test.
        client_factory.clients = {}
        client_factory.resources = {}

    def test_get_number_of_instances(self):
        self.mock_docdb_service.describe_db_instances.return_value = get_docdb_instances_with_status_side_effect(3)
        result = docdb_utils.get_number_of_instances(self.session_mock, DOCDB_CLUSTER_ID)
        self.mock_docdb_service.describe_db_instances.assert_called_once_with(Filters=[
            {
                'Name': 'db-cluster-id',
                'Values': [DOCDB_CLUSTER_ID]
            },
        ])
        self.assertEqual(3, result)

    def test_get_number_of_instances_empty(self):
        self.mock_docdb_service.describe_db_instances.return_value = get_docdb_instances_with_status_side_effect(0)
        result = docdb_utils.get_number_of_instances(self.session_mock, DOCDB_CLUSTER_ID)
        self.mock_docdb_service.describe_db_instances.assert_called_once_with(Filters=[
            {
                'Name': 'db-cluster-id',
                'Values': [DOCDB_CLUSTER_ID]
            },
        ])
        self.assertEqual(0, result)

    def test_get_number_of_instances_missing_response(self):
        self.mock_docdb_service.describe_db_instances.return_value = {'DBInstances': []}
        result = docdb_utils.get_number_of_instances(self.session_mock, DOCDB_CLUSTER_ID)
        self.mock_docdb_service.describe_db_instances.assert_called_once_with(Filters=[
            {
                'Name': 'db-cluster-id',
                'Values': [DOCDB_CLUSTER_ID]
            },
        ])
        self.assertEqual(0, result)

    def test_get_instance_status(self):
        self.mock_docdb_service.describe_db_instances.return_value = get_docdb_instances_with_status_side_effect(1)
        result = docdb_utils.get_instance_status(self.session_mock, DOCDB_INSTANCE_ID)
        self.mock_docdb_service.describe_db_instances.assert_called_once_with(DBInstanceIdentifier=DOCDB_INSTANCE_ID)
        self.assertEqual('available', result.get('DBInstanceStatus'))

    def test_get_instance_status_instance_not_found(self):
        self.mock_docdb_service.describe_db_instances.return_value = {
            'DBInstances': []
        }
        self.assertRaises(Exception, docdb_utils.get_instance_status, self.session_mock, DOCDB_INSTANCE_ID)
        self.mock_docdb_service.describe_db_instances.assert_called_once_with(DBInstanceIdentifier=DOCDB_INSTANCE_ID)

    def test_get_instance_az(self):
        az = 'us-east-1b'
        self.mock_docdb_service.describe_db_instances.return_value = get_docdb_instances_side_effect(az)
        result = docdb_utils.get_instance_az(self.session_mock, DOCDB_INSTANCE_ID)
        self.mock_docdb_service.describe_db_instances.assert_called_once_with(DBInstanceIdentifier=DOCDB_INSTANCE_ID)
        self.assertEqual(result, az)

    def test_get_cluster_azs(self):
        self.mock_docdb_service.describe_db_clusters.return_value = get_describe_db_cluster_side_effect()
        self.mock_docdb_service.describe_db_subnet_groups.return_value = get_subnet_group_side_effect()
        result = docdb_utils.get_cluster_azs(self.session_mock, DOCDB_CLUSTER_ID)
        self.mock_docdb_service.describe_db_clusters.assert_called_once_with(DBClusterIdentifier=DOCDB_CLUSTER_ID)
        self.mock_docdb_service.describe_db_subnet_groups.assert_called_once_with(
            DBSubnetGroupName=DOCDB_SUBNET_GROUP_NAME)
        self.assertListEqual(result, ['us-east-1a', 'us-east-1b'])

    def test_get_cluster_members(self):
        cluster_members = [
            {'IsClusterWriter': True, 'DBInstanceIdentifier': 'instance1'},
            {'IsClusterWriter': False, 'DBInstanceIdentifier': 'instance2'}
        ]
        self.mock_docdb_service.describe_db_clusters.return_value = {
            'DBClusters': [{'DBClusterMembers': cluster_members}]
        }
        result = docdb_utils.get_cluster_members(self.session_mock, DOCDB_CLUSTER_ID)
        self.mock_docdb_service.describe_db_clusters.assert_called_once_with(DBClusterIdentifier=DOCDB_CLUSTER_ID)
        self.assertListEqual(result, cluster_members)

    def test_delete_instance(self):
        self.mock_docdb_service.delete_db_instance.return_value = {
            'DBInstance': {
                'DBInstanceIdentifier': DOCDB_INSTANCE_ID
            }
        }
        result = docdb_utils.delete_instance(self.session_mock, DOCDB_INSTANCE_ID)
        self.mock_docdb_service.delete_db_instance.assert_called_once_with(DBInstanceIdentifier=DOCDB_INSTANCE_ID)
        self.assertEqual(DOCDB_INSTANCE_ID, result)

    def test_delete_instance_not_found(self):
        """
        Delete should not fail if instance is already deleted
        """
        self.mock_docdb_service.delete_db_instance.side_effect = \
            ClientError({'Error': {'Code': 'DBInstanceNotFound'}}, "")

        result = docdb_utils.delete_instance(self.session_mock, DOCDB_INSTANCE_ID)
        self.mock_docdb_service.delete_db_instance.assert_called_once_with(DBInstanceIdentifier=DOCDB_INSTANCE_ID)
        self.assertEqual(None, result)

    def test_get_cluster_instances(self):
        api_value_mock = {
            'DBInstances': [
                {
                    'DBInstanceIdentifier': 'Id1'
                },
                {
                    'DBInstanceIdentifier': 'Id2'
                }
            ]
        }
        self.mock_docdb_service.describe_db_instances.return_value = api_value_mock
        result = docdb_utils.get_cluster_instances(self.session_mock, DOCDB_CLUSTER_ID)
        self.mock_docdb_service.describe_db_instances.assert_called_once_with(Filters=[
            {
                'Name': 'db-cluster-id',
                'Values': [DOCDB_CLUSTER_ID]
            },
        ])
        self.assertEqual(result, api_value_mock['DBInstances'])

    @patch('time.sleep')
    @patch('time.time')
    def test_delete_cluster_db_cluster_not_found_fault(self, patched_time, patched_sleep):
        mock_sleep = MockSleep()
        patched_time.side_effect = mock_sleep.time
        patched_sleep.side_effect = mock_sleep.sleep

        self.mock_docdb_service.describe_db_clusters.side_effect = \
            ClientError({'Error': {'Code': 'DBClusterNotFoundFault'}}, "")
        result = docdb_utils.delete_cluster(self.session_mock, DOCDB_CLUSTER_ID)
        self.mock_docdb_service.delete_db_cluster.assert_called_once_with(
            DBClusterIdentifier=DOCDB_CLUSTER_ID,
            SkipFinalSnapshot=True
        )
        self.assertEqual(None, result)

    @patch('time.sleep')
    @patch('time.time')
    def test_delete_cluster_with_wait(self, patched_time, patched_sleep):
        mock_sleep = MockSleep()
        patched_time.side_effect = mock_sleep.time
        patched_sleep.side_effect = mock_sleep.sleep

        cluster_members = [
            {'IsClusterWriter': True, 'DBInstanceIdentifier': 'instance1-non-existing'},
            {'IsClusterWriter': False, 'DBInstanceIdentifier': 'instance2-non-existing'}
        ]
        self.mock_docdb_service.describe_db_clusters.return_value = {
            'DBClusters': [{'DBClusterMembers': cluster_members}]
        }
        self.assertRaises(TimeoutError, docdb_utils.delete_cluster,
                          self.session_mock, DOCDB_CLUSTER_ID, True, 5)
        self.mock_docdb_service.delete_db_cluster.assert_called_once_with(
            DBClusterIdentifier=DOCDB_CLUSTER_ID,
            SkipFinalSnapshot=True
        )

    @patch('time.sleep')
    @patch('time.time')
    def test_delete_cluster_exception(self, patched_time, patched_sleep):
        mock_sleep = MockSleep()
        patched_time.side_effect = mock_sleep.time
        patched_sleep.side_effect = mock_sleep.sleep

        self.mock_docdb_service.describe_db_clusters.return_value = {}
        self.assertRaises(Exception, docdb_utils.delete_cluster, self.session_mock, DOCDB_CLUSTER_ID, True, 1)
        self.mock_docdb_service.delete_db_cluster.assert_called_once_with(
            DBClusterIdentifier=DOCDB_CLUSTER_ID,
            SkipFinalSnapshot=True
        )
        self.mock_docdb_service.describe_db_clusters.assert_called_once_with(DBClusterIdentifier=DOCDB_CLUSTER_ID)

    def test_describe_cluster(self):
        cluster = {
            'DBClusterIdentifier': DOCDB_CLUSTER_ID,
            'Status': 'available',
        }
        self.mock_docdb_service.describe_db_clusters.return_value = {
            'DBClusters': [
                cluster
            ]
        }
        result = docdb_utils.describe_cluster(self.session_mock, DOCDB_CLUSTER_ID)
        self.mock_docdb_service.describe_db_clusters.assert_called_once_with(DBClusterIdentifier=DOCDB_CLUSTER_ID)
        self.assertEqual(result, cluster)

    def test_create_snapshot(self):
        snapshot_id = 'Snapshot-1'
        self.mock_docdb_service.create_db_cluster_snapshot.return_value = {
            'DBClusterSnapshot': {
                'DBClusterSnapshotIdentifier': snapshot_id
            }
        }
        result = docdb_utils.create_snapshot(self.session_mock, DOCDB_CLUSTER_ID, snapshot_id)
        self.mock_docdb_service.create_db_cluster_snapshot.assert_called_once_with(
            DBClusterIdentifier=DOCDB_CLUSTER_ID,
            DBClusterSnapshotIdentifier=snapshot_id
        )
        self.assertEqual(result, snapshot_id)

    def test_delete_snapshot(self):
        snapshot_id = 'Snapshot-1'
        self.mock_docdb_service.delete_db_cluster_snapshot.return_value = {
            'DBClusterSnapshot': {
                'DBClusterSnapshotIdentifier': snapshot_id
            }
        }
        result = docdb_utils.delete_snapshot(self.session_mock, snapshot_id)
        self.mock_docdb_service.delete_db_cluster_snapshot.assert_called_once_with(
            DBClusterSnapshotIdentifier=snapshot_id
        )
        self.assertEqual(result, snapshot_id)

    def test_delete_snapshot_not_found(self):
        """
        Delete should not fail if snapshot is already deleted
        """
        snapshot_id = 'Snapshot-1'
        self.mock_docdb_service.delete_db_cluster_snapshot.side_effect = \
            ClientError({'Error': {'Code': 'DBClusterSnapshotNotFoundFault'}}, "")

        result = docdb_utils.delete_snapshot(self.session_mock, snapshot_id)
        self.mock_docdb_service.delete_db_cluster_snapshot.assert_called_once_with(
            DBClusterSnapshotIdentifier=snapshot_id
        )
        self.assertEqual(result, None)

    def test_is_snapshot_available_truthy(self):
        snapshot_id = 'Snapshot-1'
        self.mock_docdb_service.describe_db_cluster_snapshots.return_value = {
            'DBClusterSnapshots': [
                {
                    'Status': 'available'
                }
            ]
        }
        result = docdb_utils.is_snapshot_available(self.session_mock, snapshot_id)
        self.mock_docdb_service.describe_db_cluster_snapshots.assert_called_once_with(
            DBClusterSnapshotIdentifier=snapshot_id
        )
        self.assertEqual(True, result)

    def test_is_snapshot_available_falsy(self):
        snapshot_id = 'Snapshot-1'
        self.mock_docdb_service.describe_db_cluster_snapshots.return_value = {
            'DBClusterSnapshots': [
                {
                    'Status': 'creating'
                }
            ]
        }
        result = docdb_utils.is_snapshot_available(self.session_mock, snapshot_id)
        self.mock_docdb_service.describe_db_cluster_snapshots.assert_called_once_with(
            DBClusterSnapshotIdentifier=snapshot_id
        )
        self.assertEqual(False, result)

    def test_delete_cluster_instances_without_wait(self):
        cluster_members = [
            {'IsClusterWriter': True, 'DBInstanceIdentifier': 'instance1'},
            {'IsClusterWriter': False, 'DBInstanceIdentifier': 'instance2'}
        ]
        self.mock_docdb_service.describe_db_clusters.return_value = {
            'DBClusters': [{'DBClusterMembers': cluster_members}]
        }
        calls = [
            call(DBInstanceIdentifier='instance1'),
            call(DBInstanceIdentifier='instance2')
        ]
        docdb_utils.delete_cluster_instances(self.session_mock, DOCDB_CLUSTER_ID, False)
        self.mock_docdb_service.describe_db_clusters.assert_called_once_with(DBClusterIdentifier=DOCDB_CLUSTER_ID)
        self.mock_docdb_service.delete_db_instance.assert_has_calls(calls)

    @patch('time.sleep')
    @patch('time.time')
    def test_delete_cluster_instances_with_wait(self, patched_time, patched_sleep):
        mock_sleep = MockSleep()
        patched_time.side_effect = mock_sleep.time
        patched_sleep.side_effect = mock_sleep.sleep

        cluster_members = [
            {'IsClusterWriter': True, 'DBInstanceIdentifier': 'instance1'},
            {'IsClusterWriter': False, 'DBInstanceIdentifier': 'instance2'}
        ]
        self.mock_docdb_service.describe_db_clusters.side_effect = [{
            'DBClusters': [{'DBClusterMembers': cluster_members}]
        }, {
            'DBClusters': [{
                'DBClusterMembers': []
            }]
        }]
        delete_calls = [
            call(DBInstanceIdentifier='instance1'),
            call(DBInstanceIdentifier='instance2')
        ]
        describe_calls = [
            call(DBClusterIdentifier=DOCDB_CLUSTER_ID),
            call(DBClusterIdentifier=DOCDB_CLUSTER_ID)
        ]
        docdb_utils.delete_cluster_instances(self.session_mock, DOCDB_CLUSTER_ID, True, 1)
        self.mock_docdb_service.describe_db_clusters.assert_has_calls(describe_calls)
        self.mock_docdb_service.delete_db_instance.assert_has_calls(delete_calls)

    @patch('time.sleep')
    @patch('time.time')
    def test_delete_cluster_instances_exception(self, patched_time, patched_sleep):
        mock_sleep = MockSleep()
        patched_time.side_effect = mock_sleep.time
        patched_sleep.side_effect = mock_sleep.sleep

        cluster_members = [
            {'IsClusterWriter': True, 'DBInstanceIdentifier': 'instance1'},
            {'IsClusterWriter': False, 'DBInstanceIdentifier': 'instance2'}
        ]
        self.mock_docdb_service.describe_db_clusters.side_effect = [{
            'DBClusters': [{'DBClusterMembers': cluster_members}]
        }, {
            'DBClusters': [{'DBClusterMembers': cluster_members}]
        }]
        delete_calls = [
            call(DBInstanceIdentifier='instance1'),
            call(DBInstanceIdentifier='instance2')
        ]
        describe_calls = [
            call(DBClusterIdentifier=DOCDB_CLUSTER_ID),
            call(DBClusterIdentifier=DOCDB_CLUSTER_ID)
        ]
        self.assertRaises(Exception, docdb_utils.delete_cluster_instances, self.session_mock, DOCDB_CLUSTER_ID, True, 1)
        self.mock_docdb_service.describe_db_clusters.assert_has_calls(describe_calls)
        self.mock_docdb_service.delete_db_instance.assert_has_calls(delete_calls)
