from cfn_tools import load_yaml
from cfn_tools.odict import ODict


def loads_yaml(file_content):
    """
    Returns dict object, which represents YAML structure, for given file content.
    :param file_content The file content
    """
    return load_yaml(file_content)


def file_loads_yaml(file_path):
    """
     Returns dict object, which represents YAML structure, for given file path.
    :param file_path The file path
    """
    file = None
    try:
        file = open(file_path)
        return loads_yaml(file)
    finally:
        if file:
            file.close()


def is_equal(obj_1: ODict, obj_2: ODict):
    """
    Verifies if given dict objects are equal and returns True is equal, False otherwise
    :param obj_1 The dict object
    :param obj_2 The dict object
    """
    if obj_1 is None or obj_2 is None:
        raise Exception('Parameters [obj_1] and [obj_2] cannot be None.')
    return _ordered(obj_1.items()) == _ordered(obj_2.items())


def _ordered(obj):
    """
    Orders dict object
    :param obj The dict object to order
    """
    if isinstance(obj, ODict):
        return sorted((k, _ordered(v)) for k, v in obj.items())
    if isinstance(obj, list):
        return sorted(_ordered(x) for x in obj)
    else:
        return obj
