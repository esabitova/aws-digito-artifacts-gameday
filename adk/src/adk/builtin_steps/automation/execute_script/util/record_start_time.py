from datetime import datetime, timezone

from typing import List, Callable

from adk.src.adk.domain.data_type import DataType
from adk.src.adk.domain.output import Output
from adk.src.adk.parent_steps.automation.python_step import PythonStep


class RecordStartTime(PythonStep):
    def get_helper_functions(self) -> List[Callable]:
        return [get_current_time]

    @staticmethod
    def script_handler(params: dict, context):
        return get_current_time().isoformat()

    def get_outputs(self) -> List[Output]:
        return [Output(name='StartTime', selector='$.Payload', output_type=DataType.String)]

    def get_inputs(self) -> List[str]:
        return []

    def get_description(self) -> str:
        return "Start the timer when SOP starts"


def get_current_time():
    return datetime.now(timezone.utc)
