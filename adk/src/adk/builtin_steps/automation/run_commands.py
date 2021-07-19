from typing import List

from adk.src.adk.domain.data_type import DataType
from adk.src.adk.domain.input import Input
from adk.src.adk.parent_steps.automation.run_command_step import RunCommandStep
from adk.src.adk.parent_steps.command.run_power_shell_script import RunPowerShellScript
from adk.src.adk.parent_steps.command.run_shell_script import RunShellScript


def run_shell_script(commands: List[str], instance_ids_input: str, working_dir: str = None,
                     timeout_seconds: int = None, use_send_command=True):
    timeout = str(timeout_seconds) if timeout_seconds else None
    return RunCommandStep(
        name="AWS_RunShellScript",
        run_cmd_document_name='AWS-RunShellScript',
        command_params={
            Input("commands", DataType.StringList, "desc"): commands,
            Input("workingDirectory", DataType.String, "desc", default=""): working_dir,
            Input("executionTimeout", DataType.String, "desc", default="3600"): timeout},
        instance_ids_input=instance_ids_input,
        steps=[RunShellScript('MyRunShell',
                              inputs=['commands', 'workingDirectory', 'executionTimeout'],
                              run_commands=['{{ commands }}'],
                              working_dir_input='workingDirectory',
                              timeout_input='executionTimeout')],
        use_send_command=use_send_command)


def run_power_shell_script(self, commands: str, working_dir: str = None, timeout_seconds: int = None,
                           use_send_command=True):
    return RunCommandStep(
        name="AWS_RunShellScript",
        run_cmd_document_name='AWS-RunShellScript',
        command_params={
            Input("commands", DataType.StringList, "desc"): commands,
            Input("workingDirectory", DataType.String, "desc", default=""): working_dir,
            Input("executionTimeout", DataType.String, "desc", default="3600"): str(timeout_seconds)},
        instance_ids_input='instance-id',
        steps=[RunPowerShellScript('MyRunShell',
                                   inputs=['commands', 'workingDirectory', 'executionTimeout'],
                                   run_commands=['{{ commands }}'],
                                   working_dir_input='workingDirectory',
                                   timeout_input='executionTimeout')],
        use_send_command=use_send_command)
