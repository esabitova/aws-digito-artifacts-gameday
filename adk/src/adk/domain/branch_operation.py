import numbers
import typing
from enum import Enum


class BranchOperation(object):

    def __init__(self, operation: str, branch_type: type, func: typing.Callable[[any, any], bool]):
        self.operation = operation
        self.branch_type = branch_type
        self._func = func

    def evaluate(self, variable, constant) -> bool:
        if isinstance(variable, self.branch_type) and isinstance(variable, self.branch_type):
            return self._func(variable, constant)
        raise Exception("Type received for " + self.operation + " was not applicable to "
                        + str(self.branch_type) + ": " + variable + ", " + constant)


class Operation(Enum):
    BooleanEquals = BranchOperation("BooleanEquals", bool, lambda a, b: a == b)
    StringEquals = BranchOperation("StringEquals", str, lambda a, b: a == b)
    EqualsIgnoreCase = BranchOperation("EqualsIgnoreCase", str, lambda a, b: a.lower() == b.lower())
    EndsWith = BranchOperation("EndsWith", str, lambda var, const: var.endswith(const))
    Contains = BranchOperation("Contains", str, lambda var, const: const in var)
    NumericEquals = BranchOperation("NumericEquals", numbers.Number, lambda a, b: a == b)
    NumericGreater = BranchOperation("NumericGreater", numbers.Number, lambda var, const: var > const)
    NumericLesser = BranchOperation("NumericLesser", numbers.Number, lambda var, const: var < const)
    NumericGreaterOrEquals = \
        BranchOperation("NumericGreaterOrEquals", numbers.Number, lambda var, const: var >= const)
    NumericLesserOrEquals = \
        BranchOperation("NumericLesserOrEquals", numbers.Number, lambda var, const: var <= const)
