import unittest
import pytest
from test import test_data_provider
from unittest.mock import patch
from unittest.mock import MagicMock, call
from src.rds_util import restore_to_pit, get_cluster_writer_id, wait_cluster_failover_completed


@pytest.mark.unit_test
class TestRdsUtil(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('boto3.client')
        self.client = self.patcher.start()
        self.mock_rds = MagicMock()
        self.side_effect_map = {
            'rds': self.mock_rds
        }
        self.client.side_effect = lambda service_name: self.side_effect_map.get(service_name)
        self.mock_rds.describe_db_instances.return_value = \
            test_data_provider.get_sample_describe_db_instances_response()

    def tearDown(self):
        self.patcher.stop()

    def test_restore_to_pit(self):
        events = {}
        events['DbInstanceIdentifier'] = test_data_provider.DB_INSTANCE_ID
        events['TargetDbInstanceIdentifier'] = test_data_provider.TARGET_DB_INSTANCE_ID

        restore_output = restore_to_pit(events, None)
        self.assertEqual(str(test_data_provider.RECOVERY_POINT), restore_output['RecoveryPoint'])

    def test_restore_to_pit_fail_missing_input(self):
        events = {}
        self.assertRaises(KeyError, restore_to_pit, events, None)

    def test_restore_to_pit_fail_missing_first_input(self):
        events = {}
        events['TargetDbInstanceIdentifier'] = test_data_provider.TARGET_DB_INSTANCE_ID
        self.assertRaises(KeyError, restore_to_pit, events, None)

    def test_restore_to_pit_fail_missing_second_input(self):
        events = {}
        events['DbInstanceIdentifier'] = test_data_provider.DB_INSTANCE_ID
        self.assertRaises(KeyError, restore_to_pit, events, None)

    def test_get_cluster_writer_id_success(self):
        events = {'ClusterId': 'test_cluster_id'}
        expected_writer_id = 'writer_id_001'
        self.mock_rds.describe_db_clusters.return_value = {'DBClusters': [
            {'DBClusterMembers': [
                {'IsClusterWriter': True,
                 'DBInstanceIdentifier': expected_writer_id
                 }
            ]}]}
        actual_writer_id = get_cluster_writer_id(events, None)['WriterId']
        self.assertEqual(expected_writer_id, actual_writer_id)

    def test_wait_cluster_failover_completed_success(self):
        test_writer_id = 'writer_id_001'
        test_cluster_id = 'test_cluster_id'
        events = {'ClusterId': test_cluster_id, 'WriterId': test_writer_id}

        execution_1 = {'DBClusters': [{'Status': 'failing_over', 'DBClusterMembers':
                       [{'IsClusterWriter': True, 'DBInstanceIdentifier': test_writer_id}]}]}

        execution_2 = {'DBClusters': [{'Status': 'available', 'DBClusterMembers':
                       [{'IsClusterWriter': True, 'DBInstanceIdentifier': test_writer_id}]}]}

        execution_3 = {'DBClusters': [{'Status': 'available', 'DBClusterMembers':
                       [{'IsClusterWriter': True, 'DBInstanceIdentifier': 'failed_over_id'}]}]}

        self.mock_rds.describe_db_clusters.side_effect = [execution_1, execution_2, execution_3]
        wait_cluster_failover_completed(events, None)
        self.mock_rds.describe_db_clusters.assert_has_calls([call(DBClusterIdentifier=test_cluster_id),
                                                             call(DBClusterIdentifier=test_cluster_id),
                                                             call(DBClusterIdentifier=test_cluster_id)])
