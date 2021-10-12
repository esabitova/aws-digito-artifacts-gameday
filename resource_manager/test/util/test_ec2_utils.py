import pytest
import unittest
from unittest.mock import MagicMock, patch

import resource_manager.src.util.boto3_client_factory as client_factory
from resource_manager.src.util import ec2_utils
from documents.util.scripts.test.mock_sleep import MockSleep


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

    @patch('time.sleep')
    def test_modify_ec2_instance_type_stop_time_out_fail(self, patched_sleep):
        mock_sleep = MockSleep()
        patched_sleep.side_effect = mock_sleep.sleep
        self.assertRaises(Exception, ec2_utils.modify_ec2_instance_type,
                          self.session_mock, 'test-instance-id', 'test-instance-type')

    @patch('time.sleep')
    def test_modify_ec2_instance_type_start_time_out_fail(self, patched_sleep):
        mock_sleep = MockSleep()
        patched_sleep.side_effect = mock_sleep.sleep
        self.mock_ec2_service.describe_instance_status.return_value = \
            {'InstanceStatuses': [{'InstanceState': {'Name': 'stopped'}, }, ], }

        self.assertRaises(Exception, ec2_utils.modify_ec2_instance_type,
                          self.session_mock, 'test-instance-id', 'test-instance-type')

    @patch('time.sleep')
    def test_modify_ec2_instance_type_success(self, patched_sleep):
        mock_sleep = MockSleep()
        patched_sleep.side_effect = mock_sleep.sleep
        self.mock_ec2_service.describe_instance_status.side_effect = [
            {'InstanceStatuses': [{'InstanceState': {'Name': 'pending'}, }, ]},
            {'InstanceStatuses': [{'InstanceState': {'Name': 'stopped'}, }, ]},
            {'InstanceStatuses': [{'InstanceState': {'Name': 'pending'}, }, ]},
            {'InstanceStatuses': [{'InstanceState': {'Name': 'running'}, }, ]},
        ]

        ec2_utils.modify_ec2_instance_type(self.session_mock, 'test-instance-id', 'test-instance-type')
        self.assertEqual(self.mock_ec2_service.describe_instance_status.call_count, 4)
        self.mock_ec2_service.stop_instances.assert_called_once()
        self.mock_ec2_service.start_instances.assert_called_once()
