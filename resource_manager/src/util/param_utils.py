import re
from sttable import parse_str_table


def parse_param_values_from_table(data_table, param_containers):
    """
    Parsing given data table parameters for each row. As explained in :func:`~resource_manager.src.util.param_utils.parse_param_value`
    :param data_table The table which contains parameters to parse
    :param param_containers The containers with parameter values where parameter value references are pointing to
    """
    parameters = []
    for data_row in parse_str_table(data_table).rows:
        param_row = {}
        for param_name, value_ref in data_row.items():
            param_row[param_name] = str(parse_param_value(value_ref, param_containers))
        parameters.append(param_row)
    return parameters


def parse_param_value(param_value, param_containers):
    """
    Helper to parse/retrieve values from given parameter containers for given parameter value reference
    or simply return value if 'param_value' is not reference. Following 'param_value' format is
    considered as reference:\n
    {{<container_key>:parameter1>parameter2}}\n
    :param param_value The parameter value or parameter reference to parse value for
    :param param_containers The dict of containers based on key/value pair: {'containter_key': <data>}
    """
    param_val_ref_pattern = re.compile('{{2}.*}{2}')
    ref_match = param_val_ref_pattern.match(param_value)
    if ref_match:
        param_ref = re.search('[^{](.+):(\w+>?)+[^}]', param_value)
        if param_ref is not None and len(param_ref.group().split(':')) == 2:
            container_key = param_ref.group().split(':')[0]
            param_val_ref = param_ref.group().split(':')[1]
            container = param_containers.get(container_key)
            if container is None:
                raise Exception('Parameter container for key [{}] does not exist.'.format(container_key))
            return _get_param_value(container, param_val_ref)
        elif param_ref is None:
            raise Exception('Failed to parse [{}] parameter.'.format(param_value))
        raise Exception('Parameter format [{}] is not supported'.format(param_ref.group()))
    else:
        # In case if given value is NOT a reference pointing to cloud formation output or cache
        return param_value


def _get_param_value(param_container, param_val_ref):
    value = param_container
    params = param_val_ref.split(">")
    for i in range(len(params)):
        value = value.get(params[i])
        if value is None:
            raise Exception("Parameter reference with name [{}] does not exist.".format(param_val_ref))
    return value
