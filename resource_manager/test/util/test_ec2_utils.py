import pytest
import unittest
from unittest.mock import MagicMock

import resource_manager.src.util.boto3_client_factory as client_factory
from resource_manager.src.util import ec2_utils


@pytest.mark.unit_test
class TestEC2Util(unittest.TestCase):
    def setUp(self):
        self.session_mock = MagicMock()
        self.mock_ec2_service = MagicMock()
        self.client_side_effect_map = {
            'ec2': self.mock_ec2_service,

        }
        self.session_mock.client.side_effect = lambda service_name, config=None: \
            self.client_side_effect_map.get(service_name)

    def tearDown(self):
        # Clean client factory cache after each test.
        client_factory.clients = {}
        client_factory.resources = {}

    def test_ec2_reboot(self):
        ec2_utils.reboot_instance(self.session_mock, "i-ddd")
        self.mock_ec2_service.reboot_instances.assert_called_once()
