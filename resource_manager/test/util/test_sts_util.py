import logging
import unittest
import pytest
import resource_manager.src.util.boto3_client_factory as client_factory
from unittest.mock import MagicMock
from documents.util.scripts.test import test_data_provider
from resource_manager.src.util.sts_utils import assume_role_session

logger = logging.getLogger()
logger.setLevel(logging.INFO)


@pytest.mark.unit_test
class TestStsUtil(unittest.TestCase):

    def setUp(self):
        self.base_session_mock = MagicMock()
        self.sts_client_mock = MagicMock()
        self.side_effect_map = {
            'sts': self.sts_client_mock
        }
        self.base_session_mock.client.side_effect = lambda service_name, config=None:\
            self.side_effect_map.get(service_name)
        self.sts_client_mock.assume_role.return_value = test_data_provider.ASSUME_ROLE_RESPONSE

    def tearDown(self):
        # Clean client factory cache after each test.
        client_factory.clients = {}
        client_factory.resources = {}

    def test_assume_role_session(self):
        session = assume_role_session(test_data_provider.ROLE, self.base_session_mock)

        self.sts_client_mock.assume_role.assert_called_once()
        args = self.sts_client_mock.assume_role.call_args[1]
        self.assertEqual(test_data_provider.ROLE, args['RoleArn'])
        self.assertIsNotNone(args['RoleSessionName'])
        self.assertIsNotNone(session)
        self.assertIsNotNone(session._session._credentials.access_key, test_data_provider.ACCESS_KEY_ID)
        self.assertIsNotNone(session._session._credentials.secret_key, test_data_provider.SECRET_ACCESS_KEY)
        self.assertIsNotNone(session._session._credentials.token, test_data_provider.SESSION_TOKEN)
