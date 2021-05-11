import random
import time
import datetime
import logging

from pytest_bdd import (
    given,
    parsers, when, then
)

import resource_manager.src.constants as constants
from resource_manager.src.util import docdb_utils as docdb_utils
from resource_manager.src.util.common_test_utils import extract_param_value, put_to_ssm_test_cache
from resource_manager.src.util.param_utils import parse_param_values_from_table

cache_number_of_instances_expression = 'cache current number of instances as "{cache_property}" "{step_key}" SSM ' \
                                       'automation execution' \
                                       '\n{input_parameters}'
cache_value_expression = 'cache property "{cache_property}" in step "{step_key}" SSM automation execution' \
                         '\n{input_parameters}'
cache_az_expression = 'cache az in property "{cache_property}" in step "{step_key}" SSM automation execution' \
                      '\n{input_parameters}'
cache_cluster_az_expression = 'cache one of cluster azs in property "{cache_property}" in step "{step_key}"' \
                              '\n{input_parameters}'
cache_cluster_params_expression = 'cache cluster params includingAZ="{with_az}" in object "{cache_property}"' \
                                  ' in step "{step_key}"' \
                                  '\n{input_parameters}'
assert_azs_expression = 'assert instance AZ value "{actual_property}" at "{step_key_for_actual}" is one of ' \
                        'cluster AZs' \
                        '\n{input_parameters}'
remove_instance_expression = 'delete created instance and wait for instance deletion for "{time_to_wait}" seconds' \
                             '\n{input_parameters}'
cache_replica_id_expression = 'cache replica instance identifier as "{cache_property}" at step "{step_key}"' \
                              '\n{input_parameters}'
assert_primary_instance_expression = 'assert if the cluster member is the primary instance\n{input_parameters}'
delete_cluster_expression = 'delete replaced cluster and wait for cluster deletion for "{time_to_wait}" seconds' \
                            '\n{input_parameters}'
delete_cluster_instances_expression = 'delete replaced cluster instances and wait for their removal for ' \
                                      '"{time_to_wait}" seconds\n{input_parameters}'
wait_for_instances_availability_expression = 'wait for instances to be available for "{time_to_wait}" seconds' \
                                             '\n{input_parameters}'
cache_earliest_restorable_time_expression = 'cache earliest restorable time as "{cache_property}" ' \
                                            'in "{step_key}" step' \
                                            '\n{input_parameters}'
create_snapshot_expression = 'wait for cluster snapshot creation for "{time_to_wait}" seconds\n{input_parameters}'
delete_snapshot_expression = 'delete cluster snapshot'


@given(parsers.parse(cache_number_of_instances_expression))
@when(parsers.parse(cache_number_of_instances_expression))
@then(parsers.parse(cache_number_of_instances_expression))
def cache_number_of_instances(
        resource_manager, ssm_test_cache, boto3_session, cache_property, step_key, input_parameters
):
    cluster_id = extract_param_value(
        input_parameters, "DBClusterIdentifier", resource_manager, ssm_test_cache
    )
    number_of_instances = docdb_utils.get_number_of_instances(boto3_session, cluster_id)
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, number_of_instances)


@given(parsers.parse(cache_az_expression))
@when(parsers.parse(cache_az_expression))
@then(parsers.parse(cache_az_expression))
def get_instance_az(
        resource_manager, ssm_test_cache, boto3_session, cache_property, step_key, input_parameters
):
    instance_id = extract_param_value(
        input_parameters, "DBInstanceIdentifier", resource_manager, ssm_test_cache
    )
    instance_az = docdb_utils.get_instance_az(boto3_session, instance_id)
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, instance_az)


@given(parsers.parse(cache_value_expression))
@when(parsers.parse(cache_value_expression))
def cache_value(
        resource_manager, ssm_test_cache, boto3_session, cache_property, step_key, input_parameters
):
    value = extract_param_value(
        input_parameters, "Value", resource_manager, ssm_test_cache
    )
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, value)


@given(parsers.parse(cache_cluster_az_expression))
def cache_random_cluster_az(
        resource_manager, ssm_test_cache, boto3_session, cache_property, step_key, input_parameters
):
    cluster_id = extract_param_value(
        input_parameters, "DBClusterIdentifier", resource_manager, ssm_test_cache
    )
    cluster_azs = docdb_utils.get_cluster_azs(boto3_session, cluster_id)
    az = random.choice(cluster_azs)
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, az)


@given(parsers.parse(cache_cluster_params_expression))
@then(parsers.parse(cache_cluster_params_expression))
def cache_cluster_info(
        resource_manager, ssm_test_cache, boto3_session, with_az: str, cache_property, step_key, input_parameters
):
    cluster_id = extract_param_value(
        input_parameters, "DBClusterIdentifier", resource_manager, ssm_test_cache
    )
    cluster_info = docdb_utils.describe_cluster(boto3_session, cluster_id)
    cache_value = {
        'DBClusterIdentifier': cluster_info.get('DBClusterIdentifier'),
        'DBSubnetGroup': cluster_info.get('DBSubnetGroup'),
        'Engine': cluster_info.get('Engine'),
        'VpcSecurityGroups': cluster_info.get('VpcSecurityGroups'),
    }
    if with_az == "True":
        cache_value['AvailabilityZones'] = cluster_info.get('AvailabilityZones')
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, cache_value)


@given(parsers.parse(cache_earliest_restorable_time_expression))
@then(parsers.parse(cache_earliest_restorable_time_expression))
def cache_earliest_restorable_time(
        resource_manager, ssm_test_cache, boto3_session, cache_property, step_key, input_parameters
):
    cluster_id = extract_param_value(
        input_parameters, "DBClusterIdentifier", resource_manager, ssm_test_cache
    )
    cluster_info = docdb_utils.describe_cluster(boto3_session, cluster_id)
    restore_date = cluster_info['EarliestRestorableTime'] + datetime.timedelta(minutes=1)
    restore_date_string = restore_date.strftime('%Y-%m-%dT%H:%M:%S%z')
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, restore_date_string)


@given(parsers.parse(create_snapshot_expression))
def create_snapshot(
        resource_manager, ssm_test_cache, boto3_session, time_to_wait, input_parameters
):
    cluster_id = extract_param_value(
        input_parameters, "DBClusterIdentifier", resource_manager, ssm_test_cache
    )
    snapshot_id = cluster_id + '-' + datetime.datetime.now().strftime('%m-%d-%Y-%H-%M-%S')
    docdb_utils.create_snapshot(boto3_session, cluster_id, snapshot_id)
    start_time = time.time()
    elapsed_time = time.time() - start_time
    is_snapshot_available = docdb_utils.is_snapshot_available(boto3_session, snapshot_id)
    while is_snapshot_available is False:
        if elapsed_time > int(time_to_wait):
            raise Exception(f'Waiting for snapshot creation in cluster {cluster_id} timed out')
        time.sleep(constants.sleep_time_secs)
        is_snapshot_available = docdb_utils.is_snapshot_available(boto3_session, snapshot_id)
        elapsed_time = time.time() - start_time
    put_to_ssm_test_cache(ssm_test_cache, "before", "SnapshotId", snapshot_id)
    return True


@then(parsers.parse(assert_azs_expression))
def assert_instance_az_in_cluster_azs(
        resource_manager, ssm_test_cache, boto3_session, actual_property, step_key_for_actual, input_parameters
):
    cluster_id = extract_param_value(
        input_parameters, "DBClusterIdentifier", resource_manager, ssm_test_cache
    )
    cluster_azs = docdb_utils.get_cluster_azs(boto3_session, cluster_id)
    assert ssm_test_cache[step_key_for_actual][actual_property] in cluster_azs


@then(parsers.parse(remove_instance_expression))
def delete_instance_after_test(
        resource_manager, ssm_test_cache, boto3_session, time_to_wait, input_parameters
):
    instance_id = extract_param_value(
        input_parameters, "DBInstanceIdentifier", resource_manager, ssm_test_cache
    )
    cluster_id = extract_param_value(
        input_parameters, "DBClusterIdentifier", resource_manager, ssm_test_cache
    )
    docdb_utils.delete_instance(boto3_session, instance_id)
    is_instance_deleted = False
    start_time = time.time()
    elapsed_time = time.time() - start_time
    while is_instance_deleted is False:
        if elapsed_time > int(time_to_wait):
            raise Exception(f'Waiting for instance {instance_id} deletion in cluster {cluster_id} timed out')
        cluster_members = docdb_utils.get_cluster_members(boto3_session, cluster_id)
        temp_bool = True
        for cluster_member in cluster_members:
            temp_bool = temp_bool and cluster_member['DBInstanceIdentifier'] != instance_id
        time.sleep(constants.sleep_time_secs)
        elapsed_time = time.time() - start_time
        is_instance_deleted = temp_bool
    return True


@when(parsers.parse('Assert that DocumentDB instance is in "{expected_status}" status with timeout of '
                    '"{time_to_wait}" seconds\n{input_parameters}'))
@then(parsers.parse('Assert that DocumentDB instance is in "{expected_status}" status with timeout of '
                    '"{time_to_wait}" seconds\n{input_parameters}'))
def wait_for_documentdb_with_params(cfn_output_params, time_to_wait, boto3_session,
                                    expected_status, input_parameters, ssm_test_cache):
    """
    Common step to wait for SSM document execution step waiting of final status
    :param cfn_output_params The cfn output params from resource manager
    :param boto3_session boto3 client session
    :param time_to_wait Timeout in seconds to wait until step status is resolved
    :param expected_status The expected SSM document execution status
    :param input_parameters The input parameters
    :param ssm_test_cache The custom test cache
    """
    parameters = parse_param_values_from_table(input_parameters, {'cache': ssm_test_cache,
                                                                  'cfn-output': cfn_output_params})
    db_instance_identifier = parameters[0].get('DBInstanceIdentifier')
    if db_instance_identifier is None:
        raise Exception('Parameter with name [DBInstanceIdentifier] should be provided')

    actual_status = None
    timeout_timestamp = time.time() + int(time_to_wait)
    while time.time() < timeout_timestamp:
        actual_status = docdb_utils.get_instance_status(
            session=boto3_session,
            db_instance_identifier=db_instance_identifier).get('DBInstanceStatus')
        if actual_status == expected_status:
            break
        time.sleep(5)
    if actual_status != expected_status:
        raise AssertionError(f'Expected status {expected_status} is not equal to the actual status {actual_status} '
                             'after {time_to_wait} seconds')
    assert actual_status == expected_status


@given(parsers.parse(cache_replica_id_expression))
def cache_replica_identifier(
        resource_manager, ssm_test_cache, boto3_session, cache_property, step_key, input_parameters
):
    cluster_id = extract_param_value(
        input_parameters, "DBClusterIdentifier", resource_manager, ssm_test_cache
    )
    cluster_members = docdb_utils.get_cluster_members(boto3_session, cluster_id)
    replica_identifier = cluster_members[0]['DBInstanceIdentifier']
    for cluster_member in cluster_members:
        if cluster_member['IsClusterWriter'] is False:
            replica_identifier = cluster_member['DBInstanceIdentifier']
            break
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, replica_identifier)


@then(parsers.parse(assert_primary_instance_expression))
def assert_is_cluster_member_primary_instance(
        resource_manager, ssm_test_cache, boto3_session, input_parameters
):
    cluster_id = extract_param_value(
        input_parameters, "DBClusterIdentifier", resource_manager, ssm_test_cache
    )
    instance_id = extract_param_value(
        input_parameters, "DBInstanceIdentifier", resource_manager, ssm_test_cache
    )
    cluster_members = docdb_utils.get_cluster_members(boto3_session, cluster_id)
    is_cluster_writer = False
    for cluster_member in cluster_members:
        if cluster_member['DBInstanceIdentifier'] == instance_id and cluster_member['IsClusterWriter'] is True:
            is_cluster_writer = True
    assert is_cluster_writer


@then(parsers.parse(wait_for_instances_availability_expression))
def wait_for_instances(
        resource_manager, ssm_test_cache, boto3_session, time_to_wait, input_parameters
):
    cluster_id = extract_param_value(
        input_parameters, "DBClusterIdentifier", resource_manager, ssm_test_cache
    )
    each_instance_available = False
    start_time = time.time()
    elapsed_time = time.time() - start_time
    while each_instance_available is False:
        if elapsed_time > int(time_to_wait):
            raise Exception(f'Waiting for instances to be available in cluster {cluster_id} timed out')
        instances = docdb_utils.get_cluster_instances(boto3_session, cluster_id)
        time.sleep(constants.sleep_time_secs)
        elapsed_time = time.time() - start_time
        for instance in instances:
            logging.info(f'Found instance {instance["DBInstanceIdentifier"]}, status {instance["DBInstanceStatus"]}')
            if instance['DBInstanceStatus'] != 'available':
                each_instance_available = False
                break
            else:
                each_instance_available = True
    return True


@then(parsers.parse(delete_cluster_instances_expression))
def delete_replaced_cluster_instances(
        resource_manager, ssm_test_cache, boto3_session, time_to_wait, input_parameters
):
    cluster_id = extract_param_value(
        input_parameters, "ReplacedDBClusterIdentifier", resource_manager, ssm_test_cache
    )
    replaced_cluster_id = cluster_id + "-replaced"
    docdb_utils.delete_cluster_instances(boto3_session, replaced_cluster_id, True, time_to_wait)
    return True


@then(parsers.parse(delete_cluster_expression))
def delete_replaced_cluster(
        resource_manager, ssm_test_cache, boto3_session, time_to_wait, input_parameters
):
    cluster_id = extract_param_value(
        input_parameters, "DBClusterIdentifier", resource_manager, ssm_test_cache
    )
    replaced_cluster_id = cluster_id + "-replaced"
    docdb_utils.delete_cluster(boto3_session, replaced_cluster_id, True, time_to_wait)
    return True


@then(parsers.parse(delete_snapshot_expression))
def delete_cluster_snapshot(
        resource_manager, ssm_test_cache, boto3_session
):
    snapshot_id = ssm_test_cache["before"]['SnapshotId']
    docdb_utils.delete_snapshot(boto3_session, snapshot_id)
