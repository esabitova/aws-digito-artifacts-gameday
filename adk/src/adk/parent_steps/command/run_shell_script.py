import subprocess
import sys
from typing import List
import json

from adk.src.adk.domain.platform import Platform
from adk.src.adk.parent_steps.abstract_command_step import AbstractCommandStep


class RunShellScript(AbstractCommandStep):
    MAX_TIMEOUT = sys.maxsize

    def __init__(self, name: str, inputs: List[str], run_commands: List[str],
                 timeout_seconds: int = None, working_dir: str = None,
                 timeout_input: str = None, working_dir_input: str = None):
        super().__init__(name)
        if timeout_input is not None and timeout_seconds is not None:
            raise Exception('Cannot specify both a timeout_input AND a timeout_seconds but both supplied ')
        if working_dir_input is not None and working_dir is not None:
            raise Exception('Cannot specify both a working_dir_input AND a working_dir but both supplied ')
        if working_dir_input and working_dir_input not in inputs:
            raise Exception(str(working_dir_input) + ' must be declared as an input but was not: ' + str(inputs))
        if timeout_input and timeout_input not in inputs:
            raise Exception(str(timeout_input) + ' must be declared as an input but was not: ' + str(inputs))
        self._inputs = inputs
        self._run_commands = run_commands
        self._script_timeout_seconds = timeout_seconds
        self._working_dir = working_dir
        self._timeout_input = timeout_input
        self._working_dir_input = working_dir_input

    def get_supported_platforms(self):
        return [Platform.Linux]

    def get_inputs(self) -> List[str]:
        return self._inputs

    def get_description(self) -> str:
        return ''

    def execute_step(self, params: dict) -> dict:
        if type(subprocess.run).__name__ != 'MagicMock':
            confirmation = input("You are about to execute a non-mocked command against shell. "
                                 "\n\n" + self.get_command(params) + "\n\n"
                                 "Please confirm (y/n):\n")
            if confirmation != 'y':
                raise Exception('Be sure to mock out calls against shell or confirm that you are aware of risk.')

        ret = subprocess.run(self.get_command(params),
                             capture_output=True, shell=True, timeout=int(self._get_timeout(params)))
        print(ret.stdout.decode())
        return {}

    def get_command(self, params: dict):
        commands = [self.replace_variables(command, params) for command in self._run_commands]
        flattened_commands = self.flatten(commands)
        return self._get_cd_command(params) + '\n'.join(flattened_commands)

    def _get_timeout(self, params: dict):
        if self._timeout_input:
            return params[self._timeout_input]
        return self._script_timeout_seconds if self._script_timeout_seconds else RunShellScript.MAX_TIMEOUT

    def _get_cd_command(self, params: dict):
        if self._working_dir_input:
            return 'cd ' + params[self._working_dir_input] + '\n'
        return 'cd ' + self._working_dir + '\n' if self._working_dir else ''

    def get_yaml(self) -> str:
        inputs = {'runCommand': self._run_commands}
        if self._working_dir:
            inputs.update({'workingDirectory': self._working_dir})
        if self._working_dir_input:
            inputs.update({'workingDirectory': '{{ ' + self._working_dir_input + ' }}'})
        if self._script_timeout_seconds:
            inputs.update({'timeoutSeconds': self._script_timeout_seconds})
        if self._timeout_input:
            inputs.update({'timeoutSeconds': '{{ ' + self._timeout_input + ' }}'})
        return self.to_yaml(inputs=inputs)

    def get_action(self) -> str:
        return 'aws:runShellScript'

    @staticmethod
    def flatten(commands):
        flattened_commands = []
        for command in commands:
            try:
                flattened_commands.extend(json.loads(command))
            except Exception:
                flattened_commands.append(command)
        return flattened_commands
