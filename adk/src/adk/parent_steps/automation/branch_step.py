from typing import List

from adk.src.adk.domain.choice import Choice
from adk.src.adk.domain.output import Output
from adk.src.adk.parent_steps.abstract_automation_step import AbstractAutomationStep


class BranchStep(AbstractAutomationStep):
    """
    aws:branch implementation.
    Branch step that allows branching based on input param "input_to_test".
    If input_to_test is True, the execution will skip forward to skip_forward_step.
    If input_to_test is False, the execution will proceed to the next declared step.
    This class is NOT meant to be subclassed. Use as is for any aws:branch usages.
    """

    def __init__(self, name: str, choices: List[Choice], description="", default_step: AbstractAutomationStep = None):
        super().__init__(name=name)
        self.choices = choices
        self._description = description
        self._default_step = default_step

    def get_action(self) -> str:
        return 'aws:branch'

    def get_name(self) -> str:
        return self.name

    def get_description(self) -> str:
        return self._description

    def get_outputs(self) -> List[Output]:
        return []

    def get_inputs(self) -> list:
        return [choice.input_to_test for choice in self.choices]

    @staticmethod
    def execute_step(params):
        return {}

    def invoke(self, params):
        self.validations()
        params.setdefault("python_simulation_steps", [])
        params["python_simulation_steps"].append(self.name)
        if not set(self.get_inputs()) <= params.keys():
            raise Exception("Inputs were not available " + str(self.get_inputs()))
        for choice in self.choices:
            if choice.evaluate(params[choice.input_to_test]):
                print("Branch step forwarding to step " + choice.skip_to.name)
                choice.skip_to.invoke(params)
                return
        fallback = self._default_step if self._default_step else self._next_step
        print("Branch proceeding to step " + fallback.name)
        fallback.invoke(params)

    def get_yaml(self) -> str:
        choices_inputs = {"Choices": [choice.get_as_dict() for choice in self.choices]}
        if self._default_step:
            choices_inputs['Default'] = self._default_step.name
        return self.to_yaml(inputs=choices_inputs)

    def validations(self):
        super().validations()
        if self.get_next_step() is None:
            raise Exception('Branch must define a next step. But no next step was defined!')
        upcoming_steps = []
        next_step = self.get_next_step()
        while next_step is not None:
            upcoming_steps.append(next_step)
            next_step = next_step.get_next_step()
        branch_steps = [choice.skip_to for choice in self.choices]
        if not set(branch_steps) <= set(upcoming_steps):
            step_names = [step.name for step in set(branch_steps).difference(set(upcoming_steps))]
            raise Exception('Attempting to use steps in branch that are not upcoming: ' + str(step_names))
