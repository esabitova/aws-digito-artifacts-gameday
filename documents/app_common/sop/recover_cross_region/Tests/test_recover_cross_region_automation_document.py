import unittest

import pytest

from documents.app_common.sop.recover_cross_region.python.automation_document import get_automation_doc


def expected_steps(script_name, use_automation=False):
    if use_automation:
        return [script_name, f'{script_name}_ExecuteAutomation', f'{script_name}_SkipDescribe']
    return [script_name, f'{script_name}_Describe']


@pytest.mark.unit_test
class TestRunner(unittest.TestCase):

    def test_run_automation_should_succeed(self):
        output = get_automation_doc().run_automation({'AutomationAssumeRole': 'MyRule'})

        self.assertTrue('OutputRecoveryTime.RecoveryTime' in output, "Expected Automation to compute "
                                                                     "OutputRecoveryTime.RecoveryTime")
        self.assertEqual(['RecordStartTime',
                          *expected_steps('FenceSourceRegion'),
                          *expected_steps('RecoverState'),
                          *expected_steps('ScaleUpComponents'),
                          *expected_steps('Verification'),
                          *expected_steps('UpdateGlobalServices'),
                          *expected_steps('FailBack'),
                          'OutputRecoveryTime'],
                         output['python_simulation_steps'])

    def test_run_automation_should_succeed_when_passing_Automation(self):
        output = get_automation_doc().run_automation({'AutomationAssumeRole': 'MyRule',
                                                      'FenceSourceRegionAutomation': 'DummyAutomation'})

        self.assertTrue('OutputRecoveryTime.RecoveryTime' in output, "Expected Automation to compute "
                                                                     "OutputRecoveryTime.RecoveryTime")
        self.assertEqual(['RecordStartTime',
                          *expected_steps('FenceSourceRegion', True),
                          *expected_steps('RecoverState'),
                          *expected_steps('ScaleUpComponents'),
                          *expected_steps('Verification'),
                          *expected_steps('UpdateGlobalServices'),
                          *expected_steps('FailBack'),
                          'OutputRecoveryTime'],
                         output['python_simulation_steps'])

    def test_run_automation_should_succeed_when_passing_all_automation(self):
        output = get_automation_doc().run_automation({'AutomationAssumeRole': 'MyRule',
                                                      'FenceSourceRegionAutomation': 'DummyAutomation',
                                                      'RecoverStateAutomation': 'DummyAutomation',
                                                      'ScaleUpComponentsAutomation': 'DummyAutomation',
                                                      'UpdateGlobalServicesAutomation': 'DummyAutomation',
                                                      'VerificationAutomation': 'DummyAutomation',
                                                      'FailBackAutomation': 'Dummy'
                                                      })

        self.assertTrue('OutputRecoveryTime.RecoveryTime' in output, "Expected Automation to compute "
                                                                     "OutputRecoveryTime.RecoveryTime")
        self.assertEqual(['RecordStartTime',
                          *expected_steps('FenceSourceRegion', True),
                          *expected_steps('RecoverState', True),
                          *expected_steps('ScaleUpComponents', True),
                          *expected_steps('Verification', True),
                          *expected_steps('UpdateGlobalServices', True),
                          *expected_steps('FailBack', True),
                          'OutputRecoveryTime'],
                         output['python_simulation_steps'])
