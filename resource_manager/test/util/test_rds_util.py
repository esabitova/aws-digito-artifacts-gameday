import datetime
import pytest
import unittest
from unittest.mock import MagicMock

import resource_manager.src.util.boto3_client_factory as client_factory
import resource_manager.src.util.rds_util as rds_util


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

    def test_get_instance(self):
        instance_id = 'db-instance-1'
        self.mock_rds_service.describe_db_instances.return_value = {
            'DBInstances': [{
                'DBInstanceIdentifier': 'db-instance-1',
                'DBInstanceClass': 'db.t3.small', 'Engine': 'mysql',
                'DBInstanceStatus': 'available',
                'InstanceCreateTime': datetime.datetime(2021, 7, 28, 7, 57, 12,
                                                        592000)
            }]
        }
        instance = rds_util.get_db_instance_by_id(instance_id, self.session_mock)
        self.assertEqual(datetime.datetime(2021, 7, 28, 7, 57, 12, 592000), instance['InstanceCreateTime'])

    def test_delete_db_instance_async_success(self):
        instance_id = 'db-instance-1'
        rds_util.delete_db_instance(self.session_mock, instance_id, async_mode=True)
        self.mock_rds_service.delete_db_instance.assert_called_once()
        self.mock_rds_service.get_waiter.assert_not_called()

    def test_delete_db_instance_success(self):
        instance_id = 'db-instance-1'
        rds_util.delete_db_instance(self.session_mock, instance_id, async_mode=False)
        self.mock_rds_service.delete_db_instance.assert_called_once()
        self.mock_rds_service.get_waiter.assert_called_once()
