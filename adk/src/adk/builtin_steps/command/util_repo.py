from adk.src.adk.parent_steps.command.run_power_shell_script import RunPowerShellScript
from adk.src.adk.parent_steps.command.run_shell_script import RunShellScript


def get_aws_run_shell_script():
    return RunShellScript(
        name='AWS-RunShellScript',
        inputs=['commands', 'workingDirectory', 'executionTimeout'],
        run_commands=['{{ commands }}'],
        working_dir_input='workingDirectory',
        timeout_input='executionTimeout')


def get_aws_run_power_shell_script():
    return RunPowerShellScript(
        name='AWS-RunPowerShellScript',
        inputs=['commands', 'workingDirectory', 'executionTimeout'],
        run_commands=['{{ commands }}'],
        working_dir_input='workingDirectory',
        timeout_input='executionTimeout')
