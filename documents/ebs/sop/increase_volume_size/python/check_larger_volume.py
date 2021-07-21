from typing import List, Callable

from adk.src.adk.domain.data_type import DataType
from adk.src.adk.domain.output import Output
from adk.src.adk.parent_steps.automation.python_step import PythonStep


class CheckLargerVolume(PythonStep):
    def get_helper_functions(self) -> List[Callable]:
        return []

    @staticmethod
    def script_handler(params: dict, context):
        return params['CurrentSizeGiB'] >= params['SizeGib']

    def get_outputs(self) -> List[Output]:
        return [Output(name='VolumeAlreadyGreater', selector='$.Payload', output_type=DataType.Boolean)]

    def get_inputs(self) -> List[str]:
        return ['SizeGib', 'DescribeVolume.CurrentSizeGiB']

    def get_description(self) -> str:
        return 'Check if requested volume size is greater than current. If not, we know to skip to the end.'
