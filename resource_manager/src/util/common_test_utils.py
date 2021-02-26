from sttable import parse_str_table

from resource_manager.src.util import param_utils as param_utils


def extract_param_value(input_parameters, param_key, resource_manager, ssm_test_cache) -> str:
    """
    Extract value of CloudFormation output parameter
    :param input_parameters: the table with input parameters
    :param param_key: the column name in the table with input parameters
    :param resource_manager: AWS resource manager
    :param ssm_test_cache: cache
    :return: extracted value of CloudFormation output parameter
    """
    param_val_ref = parse_str_table(input_parameters).rows[0][param_key]
    cf_output = resource_manager.get_cfn_output_params()
    param_value = param_utils.parse_param_value(param_val_ref, {'cfn-output': cf_output, 'cache': ssm_test_cache})
    return param_value


def put_to_ssm_test_cache(ssm_test_cache: dict, cache_key, cache_property, value):
    """
    Put the value to the cache with the key cache property which should be placed under other key - cache_key
    :param ssm_test_cache: cache
    :param cache_key: 1-level cache key
    :param cache_property: 2-level cache key
    :param value: 2-level cache value
    """
    if cache_key in ssm_test_cache:
        cache_by_key: dict = ssm_test_cache.get(cache_key)
        cache_by_key[cache_property] = value
    else:
        ssm_test_cache[cache_key] = {cache_property: value}
