import unittest
import pytest
from unittest.mock import MagicMock
import resource_manager.src.util.boto3_client_factory as client_factory
import resource_manager.src.util.iam_utils as iam_utils
from documents.util.scripts.test.test_data_provider import get_sample_role


@pytest.mark.unit_test
class TestIamUtil(unittest.TestCase):

    def setUp(self):
        self.session_mock = MagicMock()
        self.mock_iam_service = MagicMock()
        self.client_side_effect_map = {
            'iam': self.mock_iam_service
        }
        self.session_mock.client.side_effect = lambda service_name, config=None: \
            self.client_side_effect_map.get(service_name)

    def tearDown(self):
        # Clean client factory cache after each test.
        client_factory.clients = {}
        client_factory.resources = {}

    def test_get_role_by_name(self):
        role_name = "TestRole"
        mock_role_result = {
            "Role": {
                "RoleName": "TestRole"
            }
        }
        self.mock_iam_service.get_role.return_value = get_sample_role(role_name)
        result = iam_utils.get_role_by_name(self.session_mock, role_name)
        self.mock_iam_service.get_role.assert_called_once_with(RoleName=role_name)
        self.assertEqual(result['Role']['RoleName'], mock_role_result['Role']['RoleName'])
