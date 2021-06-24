import unittest
from unittest.mock import patch, MagicMock
from documents.ebs.sop.restore_from_backup.python.automation_document import get_automation_doc
import pytest

from dateutil import parser


@pytest.mark.unit_test
class TestRunner(unittest.TestCase):

    def setUp(self):
        self.patcher = patch('boto3.client')
        self.client = self.patcher.start()
        self.mock_autoscaling = MagicMock()
        self.mock_ec2 = MagicMock()
        self.side_effect_map = {
            'autoscaling': self.mock_autoscaling,
            'ec2': self.mock_ec2
        }
        self.client.side_effect = lambda service_name, config=None: self.side_effect_map.get(service_name)
        self.mock_ec2.describe_snapshots.return_value = {'Snapshots': [{
            'VolumeId': "MyVolume",
            'State': "State",
            'StartTime': parser.parse("2019-02-28T21:28:32.000Z")
        }]}
        self.mock_ec2.create_volume.return_value = {'VolumeId': "NewVolumeId"}

    def tearDown(self):
        self.patcher.stop()

    def test_run_automation_should_succeed(self):
        self.mock_ec2.describe_volumes.return_value = {'Volumes': [
            {'VolumeType': 'io2', 'Iops': 30, 'State': 'available'}]}

        step_input = {
            'TargetAvailabilityZone': 'us-east-2a',
            'EBSSnapshotIdentifier': 'MySnapshotId',
            'VolumeIOPS': 4,
            'AutomationAssumeRole': 'MyAutomation'
        }
        output = get_automation_doc().run_automation(step_input)

        self.assertEqual("io2", output['CalculateIopsAndVolType.TargetVolumeType'])
        self.assertEqual(4, output['CalculateIopsAndVolType.TargetVolumeIOPS'])
        self.assertEqual(self.mock_ec2.describe_volumes.call_count, 2)
        self.mock_ec2.create_volume.assert_called_with(
            SnapshotId='MySnapshotId', AvailabilityZone='us-east-2a', VolumeType='io2', Iops=4)
        self.mock_ec2.describe_snapshots.assert_called_once()
        self.assertEqual(['RecordStartTime', 'EbsDescribeSnapshot', 'CalculateIopsAndVolType', 'CreateEbsVolume',
                          'WaitUntilVolumeAvailable', 'OutputRecoveryTime'], output['python_simulation_steps'])

    def test_run_automation_should_default_iops(self):
        self.mock_ec2.describe_volumes.return_value = {'Volumes': [
            {'VolumeType': 'io2', 'Iops': 30, 'State': 'available'}]}

        step_input = {
            'TargetAvailabilityZone': 'us-east-2a',
            'EBSSnapshotIdentifier': 'MySnapshotId',
            'VolumeIOPS': 0,
            'AutomationAssumeRole': 'MyAutomation'
        }
        output = get_automation_doc().run_automation(step_input)

        self.assertEqual(30, output['CalculateIopsAndVolType.TargetVolumeIOPS'])
        self.mock_ec2.create_volume.assert_called_with(
            SnapshotId='MySnapshotId', AvailabilityZone='us-east-2a', VolumeType='io2', Iops=30)
