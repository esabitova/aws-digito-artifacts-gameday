import unittest
from unittest.mock import patch, MagicMock, call
import pytest

from documents.ebs.sop.increase_volume_size.python.wait_for_volume_size import WaitForVolumeSize


@pytest.mark.unit_test
class TestWaitForVolumeSize(unittest.TestCase):

    def setUp(self):
        self.patcher = patch('boto3.client')
        self.client = self.patcher.start()
        self.mock_ssm = MagicMock()
        self.mock_ec2 = MagicMock()
        self.side_effect_map = {
            'ec2': self.mock_ec2
        }
        self.client.side_effect = lambda service_name, config=None: self.side_effect_map.get(service_name)

        self.mock_ec2.describe_volumes.side_effect = [{'Volumes': [{'Size': 11}]}]

    def tearDown(self):
        self.patcher.stop()

    def test_increase_volume_with_bigger_size(self):
        WaitForVolumeSize().execute_step({'VolumeId': 'vol-0640b62a418d54e80', 'SizeGib': 11})
        self.mock_ec2.describe_volumes.assert_has_calls([call(VolumeIds=['vol-0640b62a418d54e80'])])
