import random

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


def generate_different_value_by_ranges(from_range: int, to_range: int, old_value: int) -> int:
    """
    Generate different string value by ranges
    :param from_range: from range
    :param to_range: to range inclusively
    :param old_value: new value will not be equal to old_value
    :return: generated new value
    """
    new_value = random.randint(from_range, to_range)
    while new_value == old_value:
        new_value = random.randint(from_range, to_range)
    return new_value


def generate_and_cache_different_value_by_property_name(resource_manager, ssm_test_cache, old_property, from_range,
                                                        to_range, cache_property, cache_key, input_parameters):
    """
    Extract value of property, generate different value that extracted by ranges and put result in cache
    with the key cache_property which should be placed under other key - cache_key
    :param resource_manager: AWS resource manager
    :param ssm_test_cache: cache
    :param old_property: CloudFormation output parameter to extract value
    :param from_range: from range
    :param to_range: to range inclusively
    :param cache_key: 1-level cache key
    :param cache_property: 2-level cache key
    :param input_parameters: the table with input parameters
    """
    old_value = extract_param_value(input_parameters, old_property, resource_manager, ssm_test_cache)
    cache_value = generate_different_value_by_ranges(int(from_range), int(to_range), int(old_value))
    put_to_ssm_test_cache(ssm_test_cache, cache_key, cache_property, cache_value)


def generate_different_value_from_list(input_list: str, old_value: str) -> str:
    """
    Generate different string value from list
    :param input_list: list of values
    :param old_value: new value will not be equal to old_value
    :return: generated new value
    """
    to_list = input_list.split(",")
    print(len(to_list))
    new_value = to_list[random.randint(0, len(to_list) - 1)]
    while new_value == old_value:
        new_value = to_list[random.randint(0, len(to_list) - 1)]
    return new_value


def generate_and_cache_different_list_value_by_property_name(resource_manager, ssm_test_cache, old_property, input_list,
                                                             cache_property, cache_key, input_parameters):
    """
    Extract value of property, generate different value that extracted by ranges and put result in cache
    with the key cache_property which should be placed under other key - cache_key
    :param resource_manager: AWS resource manager
    :param ssm_test_cache: cache
    :param old_property: CloudFormation output parameter to extract value
    :param input_list: comma-separated list to take from
    :param cache_key: 1-level cache key
    :param cache_property: 2-level cache key
    :param input_parameters: the table with input parameters
    """
    old_value = extract_param_value(input_parameters, old_property, resource_manager, ssm_test_cache)
    cache_value = generate_different_value_from_list(input_list, old_value)
    put_to_ssm_test_cache(ssm_test_cache, cache_key, cache_property, cache_value)
