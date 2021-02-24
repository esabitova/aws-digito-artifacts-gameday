import random

from sttable import parse_str_table

from resource_manager.src.util import param_utils as param_utils


def generate_different_str_value_by_ranges(input_parameters, old_property, resource_manager, ssm_test_cache, from_range,
                                           to_range) -> str:
    old_value = extract_param_value(input_parameters, old_property, resource_manager, ssm_test_cache)
    new_value = random.randint(from_range, to_range)
    while new_value == old_value:
        new_value = random.randint(from_range, to_range)
    return str(new_value)


def extract_param_value(input_parameters, param_key, resource_manager, ssm_test_cache) -> str:
    """

    :rtype: object
    """
    param_val_ref = parse_str_table(input_parameters).rows[0][param_key]
    cf_output = resource_manager.get_cfn_output_params()
    param_value = param_utils.parse_param_value(param_val_ref, {'cfn-output': cf_output, 'cache': ssm_test_cache})
    return param_value


def put_to_ssm_test_cache(ssm_test_cache: dict, cache_key, cache_property, value):
    if cache_key in ssm_test_cache:
        cache_by_key: dict = ssm_test_cache.get(cache_key)
        cache_by_key[cache_property] = value
    else:
        ssm_test_cache[cache_key] = {cache_property: value}
