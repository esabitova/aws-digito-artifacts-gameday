import unittest
import pytest
import resource_manager.src.util.rds_util as rds_util
import resource_manager.src.util.boto3_client_factory as client_factory
from unittest.mock import MagicMock


@pytest.mark.unit_test
class TestRdsUtil(unittest.TestCase):

    def setUp(self):
        self.session_mock = MagicMock()
        self.mock_rds_service = MagicMock()
        self.client_side_effect_map = {
            'rds': self.mock_rds_service,

        }
        self.session_mock.client.side_effect = lambda service_name, config=None: \
            self.client_side_effect_map.get(service_name)

    def tearDown(self):
        # Clean client factory cache after each test.
        client_factory.clients = {}
        client_factory.resources = {}

    def test_get_reader_writer(self):
        db_reader_id = 'db-reader-1'
        db_writer_id = 'db-writer-1'
        self.mock_rds_service.describe_db_clusters.return_value = {'DBClusters':
                                                                   [{'DBClusterMembers':
                                                                     [{'IsClusterWriter': False,
                                                                       'DBInstanceIdentifier': db_reader_id},
                                                                      {'IsClusterWriter': True,
                                                                       'DBInstanceIdentifier': db_writer_id}]}]}
        reader, writer = rds_util.get_reader_writer('test-db-cluster-id', self.session_mock)
        self.assertEqual(db_reader_id, reader)
        self.assertEqual(db_writer_id, writer)
