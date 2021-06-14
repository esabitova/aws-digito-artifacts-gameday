from adk.src.adk.domain.data_type import DataType


class Output:

    def __init__(self, name: str, output_type: DataType, selector: str = ""):
        self.name = name
        self.output_type = output_type
        self.selector = selector or '$.' + name
