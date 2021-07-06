from datetime import datetime, timezone
from dateutil import parser

from typing import List, Callable

from adk.src.adk.domain.data_type import DataType
from adk.src.adk.domain.output import Output
from adk.src.adk.parent_steps.python_step import PythonStep


class OutputRecoveryTime(PythonStep):
    def get_helper_functions(self) -> List[Callable]:
        return [get_current_time]

    @staticmethod
    def script_handler(params: dict, context):
        return (get_current_time() - parser.parse(params['StartTime'])).seconds

    def get_outputs(self) -> List[Output]:
        return [Output(name='RecoveryTime', selector='$.Payload', output_type=DataType.Integer)]

    def get_inputs(self) -> List[str]:
        return ['RecordStartTime.StartTime']

    def get_description(self) -> str:
        return "Record the runtime in seconds"


def get_current_time():
    return datetime.now(timezone.utc)
