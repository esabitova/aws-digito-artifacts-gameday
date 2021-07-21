import unittest
from documents.ebs.sop.increase_volume_size.python.automation_document import get_automation_doc
import pytest


@pytest.mark.unit_test
class TestIncreaseVolumeSizeRealResources(unittest.TestCase):

    @unittest.skip("This hits real resources. Good for testing locally. Cannot be run during build")
    def test_increase_volume_against_real_resources(self):
        step_input = {
            'InstanceIdentifier': 'i-07ea9963f44b0c548',
            'SizeGib': 13,
            'DeviceName': '/dev/xvda',
            'Partition': '1',
            'AutomationAssumeRole': 'MyAutomation'
        }
        output = get_automation_doc().run_automation(step_input)

        self.assertEqual(['RecordStartTime', 'EbsDescribeInstance', 'DescribeVolume', 'CheckLargerVolume',
                          'SizeValidationBranch', 'ModifyVolume', 'WaitForVolumeSize', 'AWS_RunShellScript',
                          'OutputRecoveryTime'],
                         output['python_simulation_steps'])
