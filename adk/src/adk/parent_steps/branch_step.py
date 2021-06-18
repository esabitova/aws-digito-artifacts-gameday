from typing import List

from adk.src.adk.domain.output import Output
from adk.src.adk.parent_steps.step import Step


class BranchStep(Step):
    """
    aws:branch implementation.
    Branch step that allows branching based on input param "input_to_test".
    If input_to_test is True, the execution will skip forward to skip_forward_step.
    If input_to_test is False, the execution will proceed to the next declared step.
    This class is NOT meant to be subclassed. Use as is for any aws:branch usages.
    """

    def __init__(self, name: str, skip_forward_step: Step, input_to_test: str):
        super().__init__(name=name)
        self._skip_forward_step: Step = skip_forward_step
        self._input_to_test = input_to_test

    def get_action(self) -> str:
        return 'aws:branch'

    def get_name(self) -> str:
        return self.name

    def get_description(self) -> str:
        return "Branch based on " + self._input_to_test

    def get_outputs(self) -> List[Output]:
        return []

    def get_inputs(self) -> list:
        return [self._input_to_test]

    @staticmethod
    def execute_step(params):
        return {}

    def invoke(self, params):
        params.setdefault("python_simulation_steps", [])
        params["python_simulation_steps"].append(self.name)
        if not set(self.get_inputs()) <= params.keys():
            raise Exception("Inputs were not available " + str(params.keys))
        if params[self.get_inputs()[0]]:
            print("Branch step forwarding to step " + self._skip_forward_step.name)
            self._skip_forward_step.invoke(params)
        else:
            print("Branch proceeding to step " + self._next_step.name)
            self._next_step.invoke(params)

    def get_yaml(self) -> str:
        choices_inputs = {"Choices": [
            {
                'NextStep': self._next_step.name,
                'Variable': '{{' + self._input_to_test + '}}',
                'BooleanEquals': False
            }, {
                'NextStep': self._skip_forward_step.name,
                'Variable': '{{' + self._input_to_test + '}}',
                'BooleanEquals': True
            }
        ]}
        return self.to_yaml(inputs=choices_inputs)

    def validations(self):
        super().validations()
        if self.get_next_step() is None:
            raise Exception('Branch must define a next step. But no next step was defined!')
