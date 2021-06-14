from typing import List

from adk.src.adk.domain.output import Output
from adk.src.adk.parent_steps.step import Step


class PauseStep(Step):

    def __init__(self, pause_runtime: bool, name=None, description=''):
        """
        aws:pause implementation
        Pause step in SSM pauses execution until it is resumed.
        Use the pause_runtime toggle to indicate whether the python execution should actually do a pause.
        If running in a test environment the pause_runtime should most certainly be false.
        If running a test against the automation to determine real accuracy, then perhaps enable pause_runtime.
        Pro-tip: You can keep use pause_runtime=true and mock out the pause call with:
          @mock.patch('parent_steps.pause_step.PauseStep.get_input')
          def test_something(self, mocked_input):
        :param pause_runtime: indicates whether or not to pause execution and wait for keystroke to continue
        :param name: defaults to the class name (PauseStep)
        :param description: if provided will be included in the yaml
        """
        super().__init__(name if name else type(self).__name__)
        self.description = description
        self._pause_runtime = pause_runtime

    def get_outputs(self) -> List[Output]:
        return []

    def get_inputs(self) -> list:
        return []

    def get_description(self) -> str:
        return self.description

    def execute_step(self, params: dict) -> dict:
        if self._pause_runtime:
            self.get_input("'pause_runtime' flag enabled. Press Enter to continue...\n")
        return {}

    @staticmethod
    def get_input(text):
        return input(text)

    def get_yaml(self) -> str:
        return self.to_yaml(inputs={})

    def get_action(self) -> str:
        return 'aws:pause'
