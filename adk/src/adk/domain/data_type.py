from enum import Enum


class DataType(Enum):
    """
    DataTypes supported by SSM:
    https://docs.amazonaws.cn/en_us/systems-manager/latest/userguide/sysman-doc-syntax.html#top-level-properties-type
    When declaring outputs to steps or inputs to automation documents you must include the data type of the variable.
    The value of this enum is the python type attributed to the DataType.
    We validate against this to in step.py to ensure that the type received for the output matches the expected type.
    """
    String = str
    Integer = int
    Boolean = bool
    StringList = list
