from resource_manager.src.util.synthetics_utils import stop_canary_if_its_running
import unittest
from unittest.mock import MagicMock

import pytest
import resource_manager.src.util.boto3_client_factory as client_factory


GET_CANARY_RUNNING_RESPONSE = {
    'Canary': {
        'Status': {
            'State': 'RUNNING'
        }
    }
}
GET_CANARY_STOPPED_RESPONSE = {
    'Canary': {
        'Status': {
            'State': 'STOPPED'
        }
    }
}


CANARY_NAME = 'my_canary'


@pytest.mark.unit_test
class TestSyntheticsUtils(unittest.TestCase):

    def setUp(self):
        self.session_mock = MagicMock()
        self.mock_synthetics_service = MagicMock()
        self.client_side_effect_map = {
            'synthetics': self.mock_synthetics_service,

        }
        self.session_mock.client.side_effect = lambda service_name, config=None:\
            self.client_side_effect_map.get(service_name)

    def tearDown(self):
        # Clean client factory cache after each test.
        client_factory.clients = {}
        client_factory.resources = {}

    def test_stop_canary_if_its_running__running(self):
        self.mock_synthetics_service.get_canary.return_value = GET_CANARY_RUNNING_RESPONSE
        stop_canary_if_its_running(canary_name=CANARY_NAME, boto3_session=self.session_mock)

        self.mock_synthetics_service.get_canary.assert_called_with(Name=CANARY_NAME)
        self.mock_synthetics_service.stop_canary.assert_called_with(Name=CANARY_NAME)

    def test_stop_canary_if_its_running__stopped(self):
        self.mock_synthetics_service.get_canary.return_value = GET_CANARY_STOPPED_RESPONSE
        stop_canary_if_its_running(canary_name=CANARY_NAME, boto3_session=self.session_mock)

        self.mock_synthetics_service.get_canary.assert_called_with(Name=CANARY_NAME)
        self.assertFalse(self.mock_synthetics_service.stop_canary.called)
