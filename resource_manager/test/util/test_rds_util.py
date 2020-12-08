import unittest
import pytest
from unittest.mock import patch, MagicMock, call
import resource_manager.src.util.rds_util as rds_util

@pytest.mark.unit_test
class TestRdsUtil(unittest.TestCase):

    def setUp(self):
        self.client_patcher = patch('boto3.client')
        self.client = self.client_patcher.start()
        self.mock_rds_service = MagicMock()
        self.client_side_effect_map = {
            'rds': self.mock_rds_service,

        }
        self.client.side_effect = lambda service_name: self.client_side_effect_map.get(service_name)

    def tearDown(self):
        self.client_patcher.stop()

    def test_get_reader_writer(self):
        db_reader_id = 'db-reader-1'
        db_writer_id = 'db-writer-1'
        self.mock_rds_service.describe_db_clusters.return_value = {'DBClusters': [
                                                                    {'DBClusterMembers': [
                                                                        {'IsClusterWriter': False,
                                                                         'DBInstanceIdentifier': db_reader_id},
                                                                        {'IsClusterWriter': True,
                                                                         'DBInstanceIdentifier': db_writer_id}
                                                                      ]}
                                                                    ]}
        reader, writer = rds_util.get_reader_writer('test-db-cluster-id')
        self.assertEqual(db_reader_id, reader)
        self.assertEqual(db_writer_id, writer)

