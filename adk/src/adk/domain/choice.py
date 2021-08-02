from adk.src.adk.domain.branch_operation import BranchOperation, Operation
from adk.src.adk.parent_steps.abstract_automation_step import AutomationStepReference, AbstractAutomationStep


class Choice(object):

    def __init__(self, operation: Operation, input_to_test: str, constant, skip_to: AutomationStepReference):
        self._operation: BranchOperation = operation.value
        self._constant = constant
        self.input_to_test = input_to_test
        self.skip_to = skip_to

    def get_as_dict(self, step: AbstractAutomationStep):
        variable_name = "{{" + self.input_to_test + "}}"
        return {
            'NextStep': self.skip_to.resolve_step(step).name,
            'Variable': variable_name,
            self._operation.operation: self._constant
        }

    def evaluate(self, var):
        return self._operation.evaluate(var, self._constant)
