import unittest
import pytest
from resource_manager.src.util.role_session import RoleSession
from unittest.mock import MagicMock, patch
from datetime import datetime


@pytest.mark.unit_test
class TestRdsUtil(unittest.TestCase):

    def setUp(self):
        self.test_region_name = 'test_region_name'

        self.cred_session_mock = MagicMock()
        self.cred_session_mock.get_config_variable.return_value = self.test_region_name

        self.refresh_session_mock = MagicMock()
        self.refresh_session_mock.get_config_variable.return_value = self.test_region_name
        self.refresh_session_patcher = patch('botocore.session.Session',
                                             MagicMock(return_value=self.refresh_session_mock))
        self.refresh_session_patcher.start()

    def tearDown(self):
        self.refresh_session_patcher.stop()

    def test_role_session(self):
        sts_client = MagicMock()
        self.cred_session_mock.client.return_value = sts_client
        sts_client.assume_role.return_value = {'Credentials': {'AccessKeyId': 'xxxx',
                                                               'SecretAccessKey': 'xxxx',
                                                               'SessionToken': 'xxxx',
                                                               'Expiration': datetime(2015, 1, 1)}}
        session = RoleSession('test_iam_role', 'TestSession', credential_session=self.cred_session_mock, duration=900)
        self.assertEqual(self.test_region_name, session.region_name)
