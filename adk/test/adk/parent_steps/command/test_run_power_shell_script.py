import unittest
from unittest.mock import patch

import pytest

from adk.src.adk.parent_steps.command.run_power_shell_script import RunPowerShellScript


@pytest.mark.unit_test
class TestRunPowerShellScript(unittest.TestCase):

    @patch('subprocess.run')
    def test_should_pause_if_true(self, mocked_subprocess):
        RunPowerShellScript(name="MyPowerShellScript",
                            timeout_seconds=2,
                            run_commands=["echo testing testing 123; echo here", "echo again"],
                            inputs=[]).invoke({})
        mocked_subprocess.assert_called_with("pwsh -Command 'echo testing testing 123; echo here\necho again'",
                                             capture_output=True, shell=True, timeout=2)

    def test_run_power_shell_yaml(self):
        shell_step_yaml = RunPowerShellScript(name="MyPowerShellScript",
                                              run_commands=["echo testing testing 123; echo here", "echo again"],
                                              inputs=[]).get_yaml()
        self.assertEqual('name: MyPowerShellScript\n'
                         'action: aws:runPowerShellScript\n'
                         'inputs:\n'
                         '  runCommand:\n'
                         '  - echo testing testing 123; echo here\n'
                         '  - echo again\n', shell_step_yaml)
