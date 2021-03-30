from pytest_bdd import (
    given,
    parsers, when, then
)
import random

from resource_manager.src.util import docdb_utils as docdb_utils
from resource_manager.src.util.common_test_utils import extract_param_value, put_to_ssm_test_cache

cache_number_of_clusters_expression = 'cache current number of clusters as "{cache_property}" "{step_key}" SSM ' \
                                      'automation execution' \
                                      '\n{input_parameters}'
cache_value_expression = 'cache property "{cache_property}" in step "{step_key}" SSM automation execution' \
                         '\n{input_parameters}'
cache_az_expression = 'cache az in property "{cache_property}" in step "{step_key}" SSM automation execution' \
                      '\n{input_parameters}'
cache_cluster_az_expression = 'cache one of cluster azs in property "{cache_property}" in step "{step_key}"' \
                              '\n{input_parameters}'
assert_azs_expression = 'assert instance AZ value "{actual_property}" at "{step_key_for_actual}" is one of ' \
                        'cluster AZs' \
                        '\n{input_parameters}'
remove_instance_expression = 'delete created instance\n{input_parameters}'
cache_replica_id_expression = 'cache replica instance identifier as "{cache_property}" at step "{step_key}"' \
                              '\n{input_parameters}'
assert_primary_instance_expression = 'assert if the cluster member is the primary instance\n{input_parameters}'


@given(parsers.parse(cache_number_of_clusters_expression))
@when(parsers.parse(cache_number_of_clusters_expression))
@then(parsers.parse(cache_number_of_clusters_expression))
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
        resource_manager, ssm_test_cache, boto3_session, input_parameters
):
    instance_id = extract_param_value(
        input_parameters, "DBInstanceIdentifier", resource_manager, ssm_test_cache
    )
    docdb_utils.delete_instance(boto3_session, instance_id)


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
