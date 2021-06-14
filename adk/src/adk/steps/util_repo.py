from adk.src.adk.parent_steps.branch_step import BranchStep
from adk.src.adk.parent_steps.pause_step import PauseStep
from adk.src.adk.parent_steps.sleep_step import SleepStep
from adk.src.adk.parent_steps.step import Step


def get_sleep_step(sleep_seconds: int, name: str = None):
    return SleepStep(sleep_seconds=sleep_seconds, name=name)


def get_pause_step(name: str = None):
    return PauseStep(pause_runtime=True, name=name)


def get_branch_step(name: str, skip_forward_step: Step, input_to_test: str):
    return BranchStep(name=name, skip_forward_step=skip_forward_step, input_to_test=input_to_test)
