import unittest
from unittest.mock import patch

import pytest

from adk.src.adk.parent_steps.branch_step import BranchStep
from adk.src.adk.parent_steps.pause_step import PauseStep
from adk.src.adk.parent_steps.sleep_step import SleepStep


@pytest.mark.unit_test
class TestYamlGeneration(unittest.TestCase):

    def setUp(self):
        sleep_step = SleepStep(3)
        branch_step = BranchStep(
            name="MyBranch",
            input_to_test="BooleanInputTest",
            skip_forward_step=sleep_step)
        branch_step.then(PauseStep(name="NextPause", pause_runtime=True)).then(sleep_step)
        self.branch_step = branch_step

    def tearDown(self):
        pass

    @patch('adk.src.adk.parent_steps.pause_step.PauseStep.get_input')
    @patch('time.sleep', return_value=None)
    def test_skip_if_true(self, mocked_sleep, mocked_input):
        self.branch_step.invoke({'BooleanInputTest': True})
        mocked_input.assert_not_called()
        mocked_sleep.assert_called_once()

    @patch('adk.src.adk.parent_steps.pause_step.PauseStep.get_input')
    @patch('time.sleep', return_value=None)
    def test_next_if_false(self, mocked_sleep, mocked_input):
        self.branch_step.invoke({'BooleanInputTest': False})
        mocked_input.assert_called_once()
        mocked_sleep.assert_called_once()

    @patch('adk.src.adk.parent_steps.pause_step.PauseStep.get_input')
    @patch('time.sleep', return_value=None)
    def test_boolean_input_not_provided_throws(self, mocked_input, mocked_time):
        self.assertRaises(Exception, self.branch_step.invoke, {})

    def test_branch_yaml(self):
        self.assertEqual(
            'description: Branch based on BooleanInputTest\n'
            'name: MyBranch\n'
            'action: aws:branch\n'
            'inputs:\n'
            '  Choices:\n'
            '  - NextStep: NextPause\n'
            '    Variable: \'{{BooleanInputTest}}\'\n'
            '    BooleanEquals: false\n'
            '  - NextStep: SleepStep\n'
            '    Variable: \'{{BooleanInputTest}}\'\n'
            '    BooleanEquals: true\n', self.branch_step.get_yaml())
