from typing import List

from adk.src.adk.domain.platform import Platform
from adk.src.adk.parent_steps.command.run_shell_script import RunShellScript


class RunPowerShellScript(RunShellScript):

    def get_supported_platforms(self):
        return [Platform.Linux, Platform.Windows]

    def get_inputs(self) -> List[str]:
        return self._inputs

    def get_description(self) -> str:
        return ''

    def get_command(self, params):
        command = super().get_command(params)
        return "pwsh -Command '" + command + "'"

    def get_action(self) -> str:
        return 'aws:runPowerShellScript'
