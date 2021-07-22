import unittest
from unittest.mock import patch, MagicMock
from documents.ebs.sop.increase_volume_size.python.automation_document import get_automation_doc
import pytest


@pytest.mark.unit_test
class TestIncreaseVolumeSize(unittest.TestCase):

    def setUp(self):
        self.patcher = patch('boto3.client')
        self.client = self.patcher.start()
        self.mock_ssm = MagicMock()
        self.mock_ec2 = MagicMock()
        self.side_effect_map = {
            'ssm': self.mock_ssm,
            'ec2': self.mock_ec2
        }
        self.client.side_effect = lambda service_name, config=None: self.side_effect_map.get(service_name)

        self.mock_ec2.describe_instances.return_value = {'Reservations': [{'Instances': [{'BlockDeviceMappings': [
            {'Ebs': {'VolumeId': 'vol-123123'}, 'DeviceName': '/dev/device'}
        ]}]}]}
        self.mock_ec2.describe_volumes.side_effect = [{'Volumes': [{'Size': 8}]}, {'Volumes': [{'Size': 10}]}]
        self.mock_ssm.get_command_invocation.return_value = {'Status': 'Success', 'ResponseCode': 0}
        self.mock_ssm.send_command.return_value = {'Command': {'CommandId': 'Command1234'}}

    def tearDown(self):
        self.patcher.stop()

    def test_increase_volume_with_bigger_size(self):
        step_input = {
            'InstanceIdentifier': 'i-07ea9963f44b0c548',
            'SizeGib': 10,
            'DeviceName': '/dev/mydevice',
            'Partition': '1',
            'AutomationAssumeRole': 'MyAutomation'
        }
        output = get_automation_doc().run_automation(step_input)

        self.assertEqual(['RecordStartTime', 'EbsDescribeInstance', 'DescribeVolume', 'CheckLargerVolume',
                          'SizeValidationBranch', 'ModifyVolume', 'WaitForVolumeSize', 'AWS_RunShellScript',
                          'OutputRecoveryTime'],
                         output['python_simulation_steps'])

        self.mock_ssm.send_command.assert_called_once_with(
            InstanceIds=['i-07ea9963f44b0c548'],
            DocumentName='AWS-RunShellScript',
            Parameters={'commands': ["originalsize=`df -h | grep /dev/mydevice | awk -F ' ' '{print $2}'`",
                                     'echo "Original volume size: ${originalsize}"',
                                     'sudo growpart /dev/mydevice 1',
                                     "mntpt=`df -h | grep /dev/mydevice | grep -oE '[^ ]+$'`",
                                     'sudo xfs_growfs -d ${mntpt} || sudo resize2fs /dev/mydevice1',
                                     'echo "Resize completed"',
                                     "volsize=`df -h | grep /dev/mydevice | awk -F ' ' '{print $2}'`",
                                     'echo "New volume size: ${volsize}"',
                                     '[ ${volsize} != ${originalsize} ] 2>/dev/null'],
                        'workingDirectory': [''],
                        'executionTimeout': ['3600']})

    def test_increase_volume_with_smaller_size_should_exit(self):
        step_input = {
            'InstanceIdentifier': 'i-07ea9963f44b0c548',
            'SizeGib': 7,
            'DeviceName': '/dev/mydevice',
            'Partition': '1',
            'AutomationAssumeRole': 'MyAutomation'
        }
        output = get_automation_doc().run_automation(step_input)

        self.assertEqual(['RecordStartTime', 'EbsDescribeInstance', 'DescribeVolume', 'CheckLargerVolume',
                          'SizeValidationBranch', 'OutputRecoveryTime'],
                         output['python_simulation_steps'])

        self.mock_ssm.send_command.assert_not_called()
