import unittest
from test import test_data_provider
from unittest.mock import patch
from unittest.mock import MagicMock

from src.rds_util import restore_to_pit

class TestRdsUtil(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('boto3.client')
        self.client = self.patcher.start()
        self.mock_rds = MagicMock()
        self.side_effect_map = {
            'rds': self.mock_rds
        }
        self.client.side_effect = lambda service_name: self.side_effect_map.get(service_name)
        self.mock_rds.describe_db_instances.return_value = test_data_provider.get_sample_describe_db_instances_response()

    def tearDown(self):
        self.patcher.stop()

    def test_restore_to_pit(self):
        events = {}
        events['DbInstanceIdentifier'] = test_data_provider.DB_INSTANCE_ID
        events['TargetDbInstanceIdentifier'] =  test_data_provider.TARGET_DB_INSTANCE_ID

        restore_output = restore_to_pit(events, None)
        self.assertEqual(str(test_data_provider.RECOVERY_POINT), restore_output['RecoveryPoint'])

    def test_restore_to_pit_fail_missing_input(self):
        events = {}
        self.assertRaises(KeyError, restore_to_pit, events, None)

    def test_restore_to_pit_fail_missing_first_input(self):
        events = {}
        events['TargetDbInstanceIdentifier'] = test_data_provider.TARGET_DB_INSTANCE_ID
        self.assertRaises(KeyError, restore_to_pit, events, None)

    def test_restore_to_pit_fail_missing_second_input(self):
        events = {}
        events['DbInstanceIdentifier'] = test_data_provider.DB_INSTANCE_ID
        self.assertRaises(KeyError, restore_to_pit, events, None)