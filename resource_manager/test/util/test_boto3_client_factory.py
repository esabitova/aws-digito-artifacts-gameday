import unittest
from unittest.mock import MagicMock
import pytest
import resource_manager.src.util.boto3_client_factory as client_factory


@pytest.mark.unit_test
class TestBoto3ClientFactory(unittest.TestCase):

    def setUp(self):
        self.session_mock = MagicMock()

    def tearDown(self):
        # Clean client factory cache after each test.
        client_factory.clients = {}
        client_factory.resources = {}

    def test_client_cache_success(self):
        client_before_cache = client_factory.client('test_client', self.session_mock)
        client_after_cache = client_factory.client('test_client', self.session_mock)
        self.assertEqual(client_before_cache, client_after_cache)
        self.session_mock.client.assert_called_once_with('test_client', config=client_factory.config)

    def test_resource_cache_success(self):
        resource_before_cache = client_factory.resource('test_client', self.session_mock)
        resource_after_cache = client_factory.resource('test_client', self.session_mock)
        self.assertEqual(resource_before_cache, resource_after_cache)
        self.session_mock.resource.assert_called_once_with('test_client', config=client_factory.config)
