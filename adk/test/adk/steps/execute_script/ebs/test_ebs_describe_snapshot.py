import datetime
import unittest
from unittest.mock import patch, MagicMock

import pytest

from adk.src.adk.steps.execute_script.ebs.ebs_describe_snapshot import EbsDescribeSnapshot


@pytest.mark.unit_test
class TestEbsDescribeSnapshot(unittest.TestCase):

    def setUp(self):
        self.patcher = patch('boto3.client')
        self.client = self.patcher.start()
        self.mock_autoscaling = MagicMock()
        self.mock_ec2 = MagicMock()
        self.side_effect_map = {
            'ec2': self.mock_ec2
        }
        self.client.side_effect = lambda service_name, config=None: self.side_effect_map.get(service_name)

    def tearDown(self):
        self.patcher.stop()

    def test_response_time_should_use_iso(self):
        params = {
            'EBSSnapshotIdentifier': 'MySnapshotId'
        }
        self.mock_ec2.describe_snapshots.return_value = {'Snapshots': [
            {'VolumeId': 'ResponseVolumeId',
             'State': 'running',
             'StartTime': datetime.datetime.fromisoformat("2021-06-20T06:38:10")}]}
        EbsDescribeSnapshot().invoke(params)
        self.assertEqual('2021-06-20T06:38:10', params['EbsDescribeSnapshot.RecoveryPoint'])
