import random
import time
import datetime
import logging
import uuid

import pytest
from botocore.exceptions import ClientError
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
cache_replica_id_expression = 'cache replica instance identifier as "{cache_property}" at step "{step_key}"' \
                              '\n{input_parameters}'
assert_primary_instance_expression = 'assert if the cluster member is the primary instance\n{input_parameters}'
wait_for_instances_availability_expression = 'wait for instances to be available for "{time_to_wait}" seconds' \
                                             '\n{input_parameters}'
cache_earliest_restorable_time_expression = 'cache earliest restorable time as "{cache_property}" ' \
                                            'in "{step_key}" step' \
                                            '\n{input_parameters}'
create_snapshot_expression = 'wait for cluster snapshot creation for "{time_to_wait}" seconds\n{input_parameters}'


@given(parsers.parse(cache_number_of_instances_expression))
@when(parsers.parse(cache_number_of_instances_expression))
@then(parsers.parse(cache_number_of_instances_expression))
def cache_number_of_instances(
        resource_pool, ssm_test_cache, boto3_session, cache_property, step_key, input_parameters
):
    cluster_id = extract_param_value(
        input_parameters, "DBClusterIdentifier", resource_pool, ssm_test_cache
    )
    number_of_instances = docdb_utils.get_number_of_instances(boto3_session, cluster_id)
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, number_of_instances)


@given(parsers.parse(cache_az_expression))
@when(parsers.parse(cache_az_expression))
@then(parsers.parse(cache_az_expression))
def get_instance_az(
        resource_pool, ssm_test_cache, boto3_session, cache_property, step_key, input_parameters
):
    instance_id = extract_param_value(
        input_parameters, "DBInstanceIdentifier", resource_pool, ssm_test_cache
    )
    instance_az = docdb_utils.get_instance_az(boto3_session, instance_id)
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, instance_az)


@given(parsers.parse(cache_value_expression))
@when(parsers.parse(cache_value_expression))
def cache_value(
        resource_pool, ssm_test_cache, boto3_session, cache_property, step_key, input_parameters
):
    value = extract_param_value(
        input_parameters, "Value", resource_pool, ssm_test_cache
    )
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, value)


@given(parsers.parse(cache_cluster_az_expression))
def cache_random_cluster_az(
        resource_pool, ssm_test_cache, boto3_session, cache_property, step_key, input_parameters
):
    cluster_id = extract_param_value(
        input_parameters, "DBClusterIdentifier", resource_pool, ssm_test_cache
    )
    cluster_azs = docdb_utils.get_cluster_azs(boto3_session, cluster_id)
    az = random.choice(cluster_azs)
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, az)


@given(parsers.parse(cache_cluster_params_expression))
@then(parsers.parse(cache_cluster_params_expression))
def cache_cluster_info(
        resource_pool, ssm_test_cache, boto3_session, with_az: str, cache_property, step_key, input_parameters
):
    cluster_id = extract_param_value(
        input_parameters, "DBClusterIdentifier", resource_pool, ssm_test_cache
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
        resource_pool, ssm_test_cache, boto3_session, cache_property, step_key, input_parameters
):
    cluster_id = extract_param_value(
        input_parameters, "DBClusterIdentifier", resource_pool, ssm_test_cache
    )
    cluster_info = docdb_utils.describe_cluster(boto3_session, cluster_id)
    restore_date = cluster_info['EarliestRestorableTime'] + datetime.timedelta(minutes=1)
    restore_date_string = restore_date.strftime('%Y-%m-%dT%H:%M:%S%z')
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, restore_date_string)


@pytest.fixture(scope='function')
def snapshot_for_teardown(boto3_session, ssm_test_cache):
    snapshot = {}
    yield snapshot
    if 'SnapshotId' in snapshot:
        snapshot_id = snapshot['SnapshotId']
        logging.info(f'Deleting snapshot {snapshot_id}')
        docdb_utils.delete_snapshot(boto3_session, snapshot_id)
        logging.info(f'Snapshot {snapshot_id} deleted')


@given(parsers.parse(create_snapshot_expression))
def create_snapshot(
        resource_pool, ssm_test_cache, boto3_session, time_to_wait, input_parameters, snapshot_for_teardown
):
    cluster_id = extract_param_value(
        input_parameters, "DBClusterIdentifier", resource_pool, ssm_test_cache
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
    snapshot_for_teardown['SnapshotId'] = snapshot_id
    return True


@then(parsers.parse(assert_azs_expression))
def assert_instance_az_in_cluster_azs(
        resource_pool, ssm_test_cache, boto3_session, actual_property, step_key_for_actual, input_parameters
):
    cluster_id = extract_param_value(
        input_parameters, "DBClusterIdentifier", resource_pool, ssm_test_cache
    )
    cluster_azs = docdb_utils.get_cluster_azs(boto3_session, cluster_id)
    assert ssm_test_cache[step_key_for_actual][actual_property] in cluster_azs


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
        resource_pool, ssm_test_cache, boto3_session, cache_property, step_key, input_parameters
):
    cluster_id = extract_param_value(
        input_parameters, "DBClusterIdentifier", resource_pool, ssm_test_cache
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
        resource_pool, ssm_test_cache, boto3_session, input_parameters
):
    cluster_id = extract_param_value(
        input_parameters, "DBClusterIdentifier", resource_pool, ssm_test_cache
    )
    instance_id = extract_param_value(
        input_parameters, "DBInstanceIdentifier", resource_pool, ssm_test_cache
    )
    cluster_members = docdb_utils.get_cluster_members(boto3_session, cluster_id)
    is_cluster_writer = False
    for cluster_member in cluster_members:
        if cluster_member['DBInstanceIdentifier'] == instance_id and cluster_member['IsClusterWriter'] is True:
            is_cluster_writer = True
    assert is_cluster_writer


@then(parsers.parse(wait_for_instances_availability_expression))
def wait_for_instances(
        resource_pool, ssm_test_cache, boto3_session, time_to_wait, input_parameters
):
    cluster_id = extract_param_value(
        input_parameters, "DBClusterIdentifier", resource_pool, ssm_test_cache
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


@pytest.fixture(scope='function')
def cluster_for_teardown(boto3_session, ssm_test_cache):
    cluster = {}
    yield cluster
    if 'ClusterId' in cluster:
        cluster_id = cluster['ClusterId']
        # Check that cluster exists before deleting
        try:
            docdb_utils.describe_cluster(boto3_session, cluster_id)
        except ClientError as error:
            if error.response['Error']['Code'] == 'DBClusterNotFoundFault':
                logging.info(f'Cluster {cluster_id} not found')
                return
        logging.info(f'Deleting cluster {cluster_id} instances')
        docdb_utils.delete_cluster_instances(boto3_session, cluster_id, True, 600)
        logging.info(f'Cluster {cluster_id} instanced deleted')
        logging.info(f'Deleting cluster {cluster_id}')
        docdb_utils.delete_cluster(boto3_session, cluster_id, True, 600)
        logging.info(f'Cluster {cluster_id} deleted')


@given(parsers.parse('prepare cluster for teardown\n{input_parameters}'))
def prepare_cluster_teardown(resource_pool, ssm_test_cache, input_parameters, cluster_for_teardown):
    cluster_id = extract_param_value(
        input_parameters, "DBClusterIdentifier", resource_pool, ssm_test_cache
    )
    replaced_cluster_id = cluster_id + "-replaced"
    cluster_for_teardown['ClusterId'] = replaced_cluster_id


@pytest.fixture(scope='function')
def instance_for_teardown(boto3_session, ssm_test_cache):
    instance = {}
    yield instance
    if 'InstanceId' in instance:
        instance_id = instance['InstanceId']
        logging.info(f'Deleting instance {instance_id}')
        docdb_utils.delete_instance(boto3_session, instance_id)
        logging.info(f'Instance {instance_id} deleted')


@given(parsers.parse('cache generated instance identifier as "{cache_property}" at step "{step_key}"'))
@then(parsers.parse('cache generated instance identifier as "{cache_property}" at step "{step_key}"'))
def cache_generated_instance_id(
        resource_pool, ssm_test_cache, cache_property, step_key, boto3_session, instance_for_teardown
):
    new_instance_id = 'docdb-replica-' + str(uuid.uuid4())
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, new_instance_id)
    instance_for_teardown['InstanceId'] = new_instance_id


@given(parsers.parse('cache cluster vpc security groups as "{cache_property}" at step "{step_key}" '
                     'SSM automation execution\n{input_parameters}'))
@then(parsers.parse('cache cluster vpc security groups as "{cache_property}" at step "{step_key}" '
                    'SSM automation execution\n{input_parameters}'))
def cache_security_groups(resource_pool, ssm_test_cache, boto3_session, cache_property, step_key, input_parameters):
    cluster_id = extract_param_value(
        input_parameters, "DBClusterIdentifier", resource_pool, ssm_test_cache
    )
    vpc_security_groups_ids = docdb_utils.get_cluster_vpc_security_groups(boto3_session, cluster_id)
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, vpc_security_groups_ids)
