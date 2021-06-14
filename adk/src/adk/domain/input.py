from typing import List

from adk.src.adk.domain.data_type import DataType


class Input(object):

    def __init__(self, name: str, input_type: DataType, description: str, default: any = None,
                 allowed_values: List[str] = None, min_items: int = 0, max_items: int = 0):
        self.name = name
        self.input_type = input_type
        self.description = description
        self.default = default
        self.allowed_values = allowed_values
        self.min_items = min_items
        self.max_items = max_items
