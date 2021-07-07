import unittest
from unittest.mock import patch, MagicMock

import pytest

from adk.src.adk.steps.execute_script.ebs.create_ebs_volume import CreateEbsVolume


@pytest.mark.unit_test
class TestCreateEbsVolume(unittest.TestCase):

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

    def test_create_volume_non_gp2(self):
        params = {
            'CalculateIopsAndVolType.TargetVolumeType': 'MyType',
            'CalculateIopsAndVolType.TargetVolumeIOPS': 'MyIops',
            'EBSSnapshotIdentifier': 'MySnapshotId',
            'TargetAvailabilityZone': 'us-east-1a'
        }
        self.mock_ec2.create_volume.return_value = {'VolumeId': "ResponseVolumeId"}
        CreateEbsVolume().invoke(params)
        self.assertEqual('ResponseVolumeId', params['CreateEbsVolume.CreatedVolumeId'])

        self.mock_ec2.create_volume.assert_called_with(SnapshotId='MySnapshotId', AvailabilityZone='us-east-1a',
                                                       VolumeType='MyType', Iops='MyIops')

    def test_create_volume_gp2(self):
        params = {
            'CalculateIopsAndVolType.TargetVolumeType': 'gp2',
            'CalculateIopsAndVolType.TargetVolumeIOPS': 'MyIops',
            'EBSSnapshotIdentifier': 'MySnapshotId',
            'TargetAvailabilityZone': 'us-east-1a'
        }
        self.mock_ec2.create_volume.return_value = {'VolumeId': "ResponseVolumeId"}
        CreateEbsVolume().invoke(params)
        self.assertEqual('ResponseVolumeId', params['CreateEbsVolume.CreatedVolumeId'])

        # Iops not included for gp2
        self.mock_ec2.create_volume.assert_called_with(SnapshotId='MySnapshotId', AvailabilityZone='us-east-1a',
                                                       VolumeType='gp2')
