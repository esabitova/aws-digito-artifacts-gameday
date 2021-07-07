import unittest

import pytest

from documents.ebs.sop.restore_from_backup.python.automation_document import get_automation_doc


@pytest.mark.unit_test
class TestOnRealResources(unittest.TestCase):

    @unittest.skip("This hits real resources. Good for testing locally. Cannot be run during build")
    def test_on_real_resources(self):
        step_input = {
            'TargetAvailabilityZone': 'us-east-2a',
            'EBSSnapshotIdentifier': 'snap-0a5a6006d1c344cfc',
            'VolumeIOPS': 350,
            'AutomationAssumeRole': 'MyAutomation'
        }
        output = get_automation_doc().run_automation(step_input)

        print("Output: " + str(output))
