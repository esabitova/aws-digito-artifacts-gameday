import unittest
import pytest
from unittest.mock import MagicMock
import resource_manager.src.util.docdb_utils as docdb_utils
from documents.util.scripts.test.test_docdb_util import get_docdb_clusters_side_effect, DOCDB_CLUSTER_ID


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
        self.mock_docdb_service.describe_db_clusters.return_value = get_docdb_clusters_side_effect(3)
        result = docdb_utils.get_number_of_instances(self.session_mock, DOCDB_CLUSTER_ID)
        self.mock_docdb_service.describe_db_clusters.assert_called_once_with(DBClusterIdentifier=DOCDB_CLUSTER_ID)
        self.assertEqual(3, result)

    def test_get_number_of_instances_empty(self):
        self.mock_docdb_service.describe_db_clusters.return_value = get_docdb_clusters_side_effect(0)
        result = docdb_utils.get_number_of_instances(self.session_mock, DOCDB_CLUSTER_ID)
        self.mock_docdb_service.describe_db_clusters.assert_called_once_with(DBClusterIdentifier=DOCDB_CLUSTER_ID)
        self.assertEqual(0, result)

    def test_get_number_of_instances_missing_response(self):
        self.mock_docdb_service.describe_db_clusters.return_value = {'DBClusters': []}
        result = docdb_utils.get_number_of_instances(self.session_mock, DOCDB_CLUSTER_ID)
        self.mock_docdb_service.describe_db_clusters.assert_called_once_with(DBClusterIdentifier=DOCDB_CLUSTER_ID)
        self.assertEqual(0, result)