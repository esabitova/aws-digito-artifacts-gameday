import unittest
from unittest.mock import MagicMock

import pytest

import resource_manager.src.util.boto3_client_factory as client_factory
from resource_manager.src.util import athena_utils

QUERY_EXECUTION_ID = "some execution id"
DELAY_SEC = 0.10
WAIT_SEC = 0.5
EXPECTED_QUERY_STATE_SUCCEEDED = "SUCCEEDED"
EXPECTED_QUERY_STATE_FAILED = "FAILED"

GET_QUERY_EXECUTION_RESPONSE_SUCCEEDED = {
    'QueryExecution': {
        'QueryExecutionId': "some execution id",
        'Status': {
            'State': 'SUCCEEDED'
        }
    }
}
GET_QUERY_EXECUTION_RESPONSE_QUEUED = {
    'QueryExecution': {
        'QueryExecutionId': "some execution id",
        'Status': {
            'State': 'QUEUED'
        }
    }
}
GET_QUERY_EXECUTION_RESPONSE_RUNNING = {
    'QueryExecution': {
        'QueryExecutionId': "some execution id",
        'Status': {
            'State': 'RUNNING'
        }
    }
}
GET_QUERY_EXECUTION_RESPONSE_FAILED = {
    'QueryExecution': {
        'QueryExecutionId': "some execution id",
        'Status': {
            'State': 'FAILED'
        }
    }
}


@pytest.mark.unit_test
class TestGlueUtil(unittest.TestCase):
    def setUp(self):
        self.mock_time = 0
        self.session_mock = MagicMock()
        self.mock_athena_service = MagicMock()
        self.client_side_effect_map = {
            'athena': self.mock_athena_service
        }

        self.session_mock.client.side_effect = lambda service_name, config=None: \
            self.client_side_effect_map.get(service_name)

    def tearDown(self):
        client_factory.clients = {}
        client_factory.resources = {}

    def test_wait_for_crawler_running_succeeded_state(self):
        self.mock_athena_service.get_query_execution.return_value = GET_QUERY_EXECUTION_RESPONSE_SUCCEEDED
        athena_utils.wait_for_query_execution(QUERY_EXECUTION_ID, self.session_mock, DELAY_SEC, WAIT_SEC,
                                              EXPECTED_QUERY_STATE_SUCCEEDED)
        self.mock_athena_service.get_query_execution.assert_called_once_with(QueryExecutionId=QUERY_EXECUTION_ID)
        self.assertEqual(1, self.mock_athena_service.get_query_execution.call_count)

    def test_wait_for_crawler_running_failed_state(self):
        self.mock_athena_service.get_query_execution.return_value = GET_QUERY_EXECUTION_RESPONSE_FAILED
        athena_utils.wait_for_query_execution(QUERY_EXECUTION_ID, self.session_mock, DELAY_SEC, WAIT_SEC,
                                              EXPECTED_QUERY_STATE_FAILED)
        self.mock_athena_service.get_query_execution.assert_called_once_with(QueryExecutionId=QUERY_EXECUTION_ID)
        self.assertEqual(1, self.mock_athena_service.get_query_execution.call_count)

    def test_wait_for_crawler_running_queued_state(self):
        self.mock_athena_service.get_query_execution.return_value = GET_QUERY_EXECUTION_RESPONSE_QUEUED
        with pytest.raises(Exception) as exception_info:
            athena_utils.wait_for_query_execution(QUERY_EXECUTION_ID, self.session_mock, DELAY_SEC, WAIT_SEC,
                                                  EXPECTED_QUERY_STATE_FAILED)
        self.mock_athena_service.get_query_execution.assert_called_with(QueryExecutionId=QUERY_EXECUTION_ID)
        self.assertTrue(exception_info.match('After 0.5 seconds the query execution is in QUEUED state'))

    def test_wait_for_crawler_running_running_state(self):
        self.mock_athena_service.get_query_execution.return_value = GET_QUERY_EXECUTION_RESPONSE_RUNNING
        with pytest.raises(Exception) as exception_info:
            athena_utils.wait_for_query_execution(QUERY_EXECUTION_ID, self.session_mock, DELAY_SEC, WAIT_SEC,
                                                  EXPECTED_QUERY_STATE_SUCCEEDED)
        self.mock_athena_service.get_query_execution.assert_called_with(QueryExecutionId=QUERY_EXECUTION_ID)
        self.assertTrue(exception_info.match('After 0.5 seconds the query execution is in RUNNING state'))
