import unittest
from unittest.mock import MagicMock

import pytest

import resource_manager.src.util.boto3_client_factory as client_factory
from resource_manager.src.util import glue_utils

GLUE_CRAWLER_NAME = "some crawler name"
DELAY_SEC = 0.10
WAIT_SEC = 0.5
GET_CRAWLER_RESPONSE_READY = {
    'Crawler': {
        'Name': 'some name',
        'State': 'READY'
    }}
GET_CRAWLER_RESPONSE_RUNNING = {
    'Crawler': {
        'Name': 'some name',
        'State': 'RUNNING'
    }}


@pytest.mark.unit_test
class TestGlueUtil(unittest.TestCase):
    def setUp(self):
        self.mock_time = 0
        self.session_mock = MagicMock()
        self.mock_glue_service = MagicMock()
        self.client_side_effect_map = {
            'glue': self.mock_glue_service
        }

        self.session_mock.client.side_effect = lambda service_name, config=None: \
            self.client_side_effect_map.get(service_name)

    def tearDown(self):
        client_factory.clients = {}
        client_factory.resources = {}

    def test_wait_for_crawler_running_ready_state(self):
        self.mock_glue_service.get_crawler.return_value = GET_CRAWLER_RESPONSE_READY
        glue_utils.wait_for_crawler_running(GLUE_CRAWLER_NAME, self.session_mock, DELAY_SEC, WAIT_SEC)
        self.mock_glue_service.get_crawler.assert_called_once_with(Name=GLUE_CRAWLER_NAME)
        self.assertEqual(1, self.mock_glue_service.get_crawler.call_count)

    def test_wait_for_crawler_running_running_state(self):
        self.mock_glue_service.get_crawler.return_value = GET_CRAWLER_RESPONSE_RUNNING
        glue_utils.wait_for_crawler_running(GLUE_CRAWLER_NAME, self.session_mock, DELAY_SEC, WAIT_SEC)
        self.mock_glue_service.get_crawler.assert_called_with(Name=GLUE_CRAWLER_NAME)
        self.assertEqual(5, self.mock_glue_service.get_crawler.call_count)
