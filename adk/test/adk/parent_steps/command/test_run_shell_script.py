import unittest
from unittest.mock import patch

import pytest

from adk.src.adk.parent_steps.command.run_shell_script import RunShellScript


@pytest.mark.unit_test
class TestRunShellScript(unittest.TestCase):

    @patch('subprocess.run')
    def test_run_shell_script(self, mocked_subprocess):
        RunShellScript(name="MyShellScript",
                       timeout_seconds=2,
                       run_commands=["echo testing testing 123; echo here", "echo again"],
                       inputs=[]).invoke({})
        mocked_subprocess.assert_called_with("echo testing testing 123; echo here\necho again",
                                             capture_output=True, shell=True, timeout=2)

    def test_should_print_yaml(self):
        shell_step_yaml = RunShellScript(name="MyShellScript",
                                         run_commands=["echo testing testing 123; echo here", "echo again"],
                                         inputs=[]).get_yaml()
        self.assertEqual('name: MyShellScript\n'
                         'action: aws:runShellScript\n'
                         'inputs:\n'
                         '  runCommand:\n'
                         '  - echo testing testing 123; echo here\n'
                         '  - echo again\n', shell_step_yaml)
