from adk.src.adk.domain.branch_operation import BranchOperation, Operation
from adk.src.adk.parent_steps.step import Step


class Choice(object):

    def __init__(self, operation: Operation, input_to_test: str, constant, skip_to: Step):
        self._operation: BranchOperation = operation.value
        self._constant = constant
        self.input_to_test = input_to_test
        self.skip_to = skip_to

    def get_as_dict(self):
        variable_name = "{{" + self.input_to_test + "}}"
        return {
            'NextStep': self.skip_to.name,
            'Variable': variable_name,
            self._operation.operation: self._constant
        }

    def evaluate(self, var):
        return self._operation.evaluate(var, self._constant)
