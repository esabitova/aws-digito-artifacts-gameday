from enum import Enum


class Operator(Enum):
    """
    Enumeration for operator
    """
    MORE_OR_EQUAL = 1,
    LESS_OR_EQUAL = 2

    @staticmethod
    def from_string(operator):
        for o in Operator:
            if o.name == operator:
                return o
        raise Exception('Operator for name [{}] is not supported.'.format(operator))
