import unittest
from unittest.mock import MagicMock
import pytest
import resource_manager.src.util.boto3_client_factory as client_factory


@pytest.mark.unit_test
class TestBoto3ClientFactory(unittest.TestCase):

    def setUp(self):
        self.session_mock = MagicMock()
        self.mock_sqs_service = MagicMock()
        self.client_side_effect_map = {
            'test_client': self.mock_sqs_service,

        }
        self.session_mock.client.side_effect = lambda service_name, config=None:\
            self.client_side_effect_map.get(service_name)

    def tearDown(self):
        # Clean client factory cache after each test.
        client_factory.clients = {}
        client_factory.resources = {}

    def test_client_cache_success(self):
        client_before_cache = client_factory.client('test_client', self.session_mock)
        client_after_cache = client_factory.client('test_client', self.session_mock)
        self.assertEqual(client_before_cache, client_after_cache)

    def test_resource_cache_success(self):
        resource_before_cache = client_factory.resource('test_client', self.session_mock)
        resource_after_cache = client_factory.resource('test_client', self.session_mock)
        self.assertEqual(resource_before_cache, resource_after_cache)
