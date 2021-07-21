import unittest

import pytest

from adk.src.adk.domain.branch_operation import Operation
from adk.src.adk.domain.choice import Choice
from adk.src.adk.parent_steps.automation.branch_step import BranchStep
from adk.src.adk.parent_steps.automation.pause_step import PauseStep


@pytest.mark.unit_test
class TestBranchStep(unittest.TestCase):

    def setUp(self):
        pause_step1 = PauseStep(name="Pause1", pause_runtime=False).is_end(True)
        pause_step2 = PauseStep(name="Pause2", pause_runtime=False).is_end(True)
        pause_step3 = PauseStep(name="Pause3", pause_runtime=False).is_end(True)
        pause_step4 = PauseStep(name="Pause4", pause_runtime=False).is_end(True)
        pause_step5 = PauseStep(name="Pause5", pause_runtime=False).is_end(True)
        branch_step = BranchStep(
            name="MyBranch",
            choices=[
                Choice(operation=Operation.BooleanEquals, input_to_test="Input1", constant=True, skip_to=pause_step1),
                Choice(operation=Operation.StringEquals, input_to_test="Input2", constant="Foo", skip_to=pause_step2),
                Choice(operation=Operation.NumericEquals, input_to_test="Input3", constant=5, skip_to=pause_step3),
                Choice(operation=Operation.NumericLesser, input_to_test="Input4", constant=5, skip_to=pause_step4)
            ],
            default_step=pause_step5)
        branch_step \
            .then(pause_step1) \
            .then(pause_step2) \
            .then(pause_step3) \
            .then(pause_step4) \
            .then(pause_step5)
        self.branch_step = branch_step

    def test_boolean_equals_choice(self):
        params = {
            'Input1': True, 'Input2': 'FooBar', 'Input3': 5, 'Input4': 5
        }
        self.branch_step.invoke(params)
        self.assertEqual(['MyBranch', 'Pause1'], params['python_simulation_steps'])

        params = {
            'Input1': False, 'Input2': 'Foo', 'Input3': 5, 'Input4': 5
        }
        self.branch_step.invoke(params)
        self.assertEqual(['MyBranch', 'Pause2'], params['python_simulation_steps'])

    def test_string_equals_choice(self):
        params = {
            'Input1': False, 'Input2': 'Foo', 'Input3': 5, 'Input4': 5
        }
        self.branch_step.invoke(params)
        self.assertEqual(['MyBranch', 'Pause2'], params['python_simulation_steps'])

        params = {
            'Input1': False, 'Input2': 'Bar', 'Input3': 5, 'Input4': 5
        }
        self.branch_step.invoke(params)
        self.assertEqual(['MyBranch', 'Pause3'], params['python_simulation_steps'])

    def test_numeric_equals(self):
        params = {
            'Input1': False, 'Input2': 'Bar', 'Input3': 5, 'Input4': 5
        }
        self.branch_step.invoke(params)
        self.assertEqual(['MyBranch', 'Pause3'], params['python_simulation_steps'])

        params = {
            'Input1': False, 'Input2': 'Bar', 'Input3': 6, 'Input4': 3
        }
        self.branch_step.invoke(params)
        self.assertEqual(['MyBranch', 'Pause4'], params['python_simulation_steps'])

    def test_numeric_lesser(self):
        params = {
            'Input1': False, 'Input2': 'Bar', 'Input3': 6, 'Input4': 3
        }
        self.branch_step.invoke(params)
        self.assertEqual(['MyBranch', 'Pause4'], params['python_simulation_steps'])

    def test_default_step(self):
        params = {
            'Input1': False, 'Input2': 'Bar', 'Input3': 6, 'Input4': 5
        }
        self.branch_step.invoke(params)
        self.assertEqual(['MyBranch', 'Pause5'], params['python_simulation_steps'])

    def test_yaml(self):
        self.assertEqual('name: MyBranch\n'
                         'action: aws:branch\n'
                         'inputs:\n'
                         '  Choices:\n'
                         '  - NextStep: Pause1\n'
                         '    Variable: \'{{Input1}}\'\n'
                         '    BooleanEquals: true\n'
                         '  - NextStep: Pause2\n'
                         '    Variable: \'{{Input2}}\'\n'
                         '    StringEquals: Foo\n'
                         '  - NextStep: Pause3\n'
                         '    Variable: \'{{Input3}}\'\n'
                         '    NumericEquals: 5\n'
                         '  - NextStep: Pause4\n'
                         '    Variable: \'{{Input4}}\'\n'
                         '    NumericLesser: 5\n'
                         '  Default: Pause5\n', self.branch_step.get_yaml())
