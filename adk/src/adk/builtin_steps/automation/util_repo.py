from adk.src.adk.domain.branch_operation import Operation
from adk.src.adk.domain.choice import Choice
from adk.src.adk.parent_steps.automation.branch_step import BranchStep
from adk.src.adk.parent_steps.automation.pause_step import PauseStep
from adk.src.adk.parent_steps.automation.sleep_step import SleepStep
from adk.src.adk.parent_steps.step import Step
from adk.src.adk.builtin_steps.automation.execute_script.util.output_recovery_time import OutputRecoveryTime
from adk.src.adk.builtin_steps.automation.execute_script.util.record_start_time import RecordStartTime


def get_sleep_step(sleep_seconds: int, name: str = None):
    return SleepStep(sleep_seconds=sleep_seconds, name=name)


def get_pause_step(name: str = None):
    return PauseStep(pause_runtime=True, name=name)


def get_boolean_branch_step(name: str, skip_forward_step: Step, boolean_input_to_test: str):
    return BranchStep(name=name, choices=[
        Choice(skip_to=skip_forward_step, input_to_test=boolean_input_to_test,
               constant=True, operation=Operation.BooleanEquals)])


def get_record_start_time_step():
    return RecordStartTime()


def get_output_recovery_time():
    return OutputRecoveryTime()
