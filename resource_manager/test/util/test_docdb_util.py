import unittest
import pytest
from unittest.mock import MagicMock
import resource_manager.src.util.docdb_utils as docdb_utils
from documents.util.scripts.test.test_docdb_util import DOCDB_CLUSTER_ID, DOCDB_INSTANCE_ID, \
    get_docdb_instances_side_effect, get_cluster_azs_side_effect, get_docdb_instances_with_status_side_effect


@pytest.mark.unit_test
class TestDocDBUtil(unittest.TestCase):

    def setUp(self):
        self.session_mock = MagicMock()
        self.mock_docdb_service = MagicMock()
        self.client_side_effect_map = {
            'docdb': self.mock_docdb_service
        }
        self.session_mock.client.side_effect = lambda service_name: self.client_side_effect_map.get(service_name)

    def tearDown(self):
        pass

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

    def test_get_instance_az(self):
        az = 'us-east-1b'
        self.mock_docdb_service.describe_db_instances.return_value = get_docdb_instances_side_effect(az)
        result = docdb_utils.get_instance_az(self.session_mock, DOCDB_INSTANCE_ID)
        self.mock_docdb_service.describe_db_instances.assert_called_once_with(DBInstanceIdentifier=DOCDB_INSTANCE_ID)
        self.assertEqual(result, az)

    def test_get_cluster_azs(self):
        self.mock_docdb_service.describe_db_clusters.return_value = get_cluster_azs_side_effect()
        result = docdb_utils.get_cluster_azs(self.session_mock, DOCDB_CLUSTER_ID)
        self.mock_docdb_service.describe_db_clusters.assert_called_once_with(DBClusterIdentifier=DOCDB_CLUSTER_ID)
        self.assertListEqual(result, ['us-east-1a', 'us-east-1b', 'us-east-1c'])
