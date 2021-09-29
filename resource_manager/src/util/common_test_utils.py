import random
import uuid

import jsonpath_ng
from boto3 import Session
from sttable import parse_str_table

from resource_manager.src.util import param_utils as param_utils
from .boto3_client_factory import client


def extract_param_value(input_parameters, param_key, resource_pool, ssm_test_cache):
    """
    Extract value of CloudFormation output parameter
    :param input_parameters: the table with input parameters
    :param param_key: the column name in the table with input parameters
    :param resource_pool: Resource pool
    :param ssm_test_cache: cache
    :return: extracted value of CloudFormation output parameter
    """
    param_val_ref = parse_str_table(input_parameters).rows[0][param_key]
    cf_output = resource_pool.get_cfn_output_params()
    param_value = param_utils.parse_param_value(param_val_ref, {'cfn-output': cf_output, 'cache': ssm_test_cache})
    return param_value


def extract_all_from_input_parameters(cf_output, cache, input_parameters, alarms):
    """
    Function to parse given input parameters based. Parameters could be of 3 types:
    * cached - in case if given parameter value is pointing to cache (Example: {{cache:valueKeyA>valueKeyB}})
    * cloud formation output - in case if given parameter value is pointing to cloud
    formation output (Example: {{output:paramNameA}})
    * simple value - in case if given parameter value is simple value
    * alarms - installed alarms
    :param cf_output - The CFN outputs
    :param cache - The cache, used to get cached values by given keys.
    :param input_parameters - The SSM input parameters as described in scenario feature file.
    :param alarms - installed alarms
    """
    input_params = parse_str_table(input_parameters).rows[0]
    parameters = {}
    for param, param_val_ref in input_params.items():
        value = param_utils.parse_param_value(param_val_ref, {'cache': cache,
                                                              'cfn-output': cf_output,
                                                              'alarm': alarms})
        parameters[param] = value
    return parameters


def extract_and_cache_param_values(input_parameters, param_list, resource_manager, ssm_test_cache, step_key):
    """
    Extract values of CloudFormation output parameters provided in table and put them into SSM cache
    :param input_parameters: the table with input parameters
    :param param_list: Coma separated column names in the table with input parameters, for 2-level cache values
    :param resource_manager: AWS resource manager
    :param ssm_test_cache: cache
    :param step_key: 1-level cache key
    """
    param_list: list = param_list.strip().split(',')
    for param_name in param_list:
        cache_value: str = extract_param_value(input_parameters, param_name, resource_manager, ssm_test_cache)
        put_to_ssm_test_cache(ssm_test_cache, step_key, param_name, cache_value)


def put_to_ssm_test_cache(ssm_test_cache: dict, cache_key, cache_property, value):
    """
    Put the value to the cache with the key cache property which should be placed under other key - cache_key
    If cache_key is None, don't create a dictionary
    :param ssm_test_cache: cache
    :param cache_key: 1-level cache key
    :param cache_property: 2-level cache key
    :param value: 2-level cache value
    """
    if not cache_key:
        ssm_test_cache[cache_property] = value
    elif cache_key in ssm_test_cache:
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


def generate_and_cache_different_value_by_property_name(resource_pool, ssm_test_cache, old_property, from_range,
                                                        to_range, cache_property, cache_key, input_parameters):
    """
    Extract value of property, generate different value that extracted by ranges and put result in cache
    with the key cache_property which should be placed under other key - cache_key
    :param resource_pool: Resource pool
    :param ssm_test_cache: cache
    :param old_property: CloudFormation output parameter to extract value
    :param from_range: from range
    :param to_range: to range inclusively
    :param cache_key: 1-level cache key
    :param cache_property: 2-level cache key
    :param input_parameters: the table with input parameters
    """
    old_value = extract_param_value(input_parameters, old_property, resource_pool, ssm_test_cache)
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


def generate_and_cache_different_list_value_by_property_name(resource_pool, ssm_test_cache, old_property, input_list,
                                                             cache_property, cache_key, input_parameters):
    """
    Extract value of property, generate different value that extracted by ranges and put result in cache
    with the key cache_property which should be placed under other key - cache_key
    :param resource_pool: Resource pool
    :param ssm_test_cache: cache
    :param old_property: CloudFormation output parameter to extract value
    :param input_list: comma-separated list to take from
    :param cache_key: 1-level cache key
    :param cache_property: 2-level cache key
    :param input_parameters: the table with input parameters
    """
    old_value = extract_param_value(input_parameters, old_property, resource_pool, ssm_test_cache)
    cache_value = generate_different_value_from_list(input_list, old_value)
    put_to_ssm_test_cache(ssm_test_cache, cache_key, cache_property, cache_value)


def assert_https_status_code_200(response: dict, error_message: str) -> None:
    if not response['ResponseMetadata']['HTTPStatusCode'] == 200:
        raise AssertionError(f'{error_message} Response is: {response}')


def assert_https_status_code_less_or_equal(code: int, response: dict, error_message: str) -> None:
    if not response['ResponseMetadata']['HTTPStatusCode'] <= code:
        raise AssertionError(f'{error_message} Response is: {response}')


def generate_random_string_with_prefix(prefix: str) -> str:
    """
    Concatenates the given prefix with a random string 8 symbols long
    :param prefix: The prefix
    """
    random_str = str(uuid.uuid1())[0:8]
    return f"{prefix}{random_str}"


def check_security_group_exists(session: Session, security_group_id: str):
    ec2_client = client('ec2', session)
    group_list = ec2_client.describe_security_groups(
        Filters=[
            {
                'Name': 'group-id',
                'Values': [security_group_id]
            },
        ]
    )
    if 'SecurityGroups' not in group_list or not group_list['SecurityGroups']:
        return False
    return True


def do_cache_by_method_of_service(cache_key, method_name, parameters, service_client, ssm_test_cache):
    """
    Cache response values by JSONPath from parameters
    :param cache_key: The cache key in ssm_test_cache
    :param method_name: The name of the AWS API method
    :param parameters: The parsed parameters with input arguments for boto3 method call and output JSONPaths
    :param service_client: The boto3 client of the service
    :return:
    """
    output_prefix = "Output-"
    input_prefix = "Input-"
    arguments = {}
    json_paths = {}
    for parameter, value in parameters.items():
        if isinstance(value, list):
            if len(value) > 1 and parameter.startswith(output_prefix):
                raise AssertionError(f'Only one JSONPath can be applied. '
                                     f'Parameter: {parameter}, value: {value}')
            # to support wrapping into the list in the
            # resource_manager.src.ssm_document.SsmDocument.parse_input_parameters
            if len(value) > 0:
                if parameter.startswith(output_prefix):
                    json_paths[parameter.replace(output_prefix, "")] = value[0]
                else:
                    arguments[parameter.replace(input_prefix, "")] = value
        else:
            if parameter.startswith(output_prefix):
                json_paths[parameter.replace(output_prefix, "")] = value
            else:
                arguments[parameter.replace(input_prefix, "")] = value
    response = getattr(service_client, method_name)(**arguments)
    for cache_property, json_path in json_paths.items():
        found = jsonpath_ng.parse(json_path).find(response)
        if found:
            # Always output as an array even len(found)==1 for the easiest processing
            target_value = [f.value for f in found]
            put_to_ssm_test_cache(ssm_test_cache, cache_key, cache_property, target_value)
