import re
from sttable import parse_str_table
from resource_manager.src.resource_model import ResourceModel


def parse_param_values_from_table(data_table, param_containers):
    """
    Parsing given data table parameters for each row. As explained in
    :func:`~resource_manager.src.util.param_utils.parse_param_value`
    :param data_table The table which contains parameters to parse
    :param param_containers The containers with parameter values where parameter value references are pointing to
    """
    parameters = []
    for data_row in parse_str_table(data_table).rows:
        param_row = {}
        for param_name, value_ref in data_row.items():
            param_row[param_name] = parse_param_value(value_ref, param_containers)
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
        param_ref = re.search(r'[^{](.+):(\w+>?)+[^}]', param_value)
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
            raise Exception("Parameter reference with name [{}] does not exist. Container {} keys are: [{}]".
                            format(param_val_ref, params[0], ','.join(param_container.keys())))
    return value


def parse_cfn_output_val_ref(cfn_output_val_ref: str) -> (str, str):
    if re.compile(r'{{2}cfn-output:(\w+>?)+}{2}').match(cfn_output_val_ref):
        param_val_ref = re.search(r'[^{cfn\-output:](\w+>?)+[^}]', cfn_output_val_ref).group()
        if param_val_ref is not None and len(param_val_ref.split('>')) == 2:
            cfn_template_name = param_val_ref.split('>')[0]
            cfn_output_param_name = param_val_ref.split('>')[1]
            return cfn_template_name, cfn_output_param_name
        else:
            raise Exception(f'Parameter format "{cfn_output_val_ref}" is not supported for [cfn-output], correct format'
                            f' is "{{cfn-output:CfnTemplateName>CfnTemplateOutputParamName}}".')
    raise Exception(f'Parameter format "{cfn_output_val_ref}" is not supported for [cfn-output], correct format'
                    f' is "{{cfn-output:CfnTemplateName>CfnTemplateOutputParamName}}".')


def parse_pool_size(custom_pool_size: str) -> dict:
    """
    Util to parse testing resource pool size from command line:
    --pool_size TestTemplateA={ON_DEMAND:3, DEDICATED:2},TestTemplateB={DEDICATED:3}
    :param custom_pool_size The custom integration test pool size
    """
    pool_size = dict()
    if custom_pool_size:
        if re.fullmatch(r'([0-9A-Za-z]+={((ON_DEMAND|DEDICATED):\d+(,)?){1,2}}(,)?)+', custom_pool_size):
            for temp_pool_size in re.finditer(r'[0-9A-Za-z]+={((ON_DEMAND|DEDICATED):\d+(,)?){1,2}}', custom_pool_size):
                template_name = temp_pool_size.group().split('=')[0]
                pool_size_config = temp_pool_size.group().split('=')[1]
                pool_size_map = {}
                for ps in re.finditer(r'((ON_DEMAND|DEDICATED):\d+)', pool_size_config):
                    rs_type = ps.group().split(":")[0]
                    rs_pool_size = ps.group().split(":")[1]
                    pool_size_map[ResourceModel.Type.from_string(rs_type)] = int(rs_pool_size)
                pool_size[template_name] = pool_size_map

        else:
            raise Exception(f'Pool size parameter format [{custom_pool_size}] is not supported. '
                            f'Expected format <cfn_template_name>={{DEDICATED:<size>,ON_DEMAND:<size>}}, example:'
                            f' --pool_size TestTemplateA={{DEDICATED:2,ON_DEMAND:1}},TestTemplateB={{ON_DEMAND:5}}')
    return pool_size
