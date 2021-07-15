from pytest_bdd import (
    given,
    parsers, when, then
)

from resource_manager.src.util.boto3_client_factory import client
from resource_manager.src.util.common_test_utils import extract_param_value
from resource_manager.src.util.common_test_utils import put_to_ssm_test_cache

cache_primary_and_replica_cluster_ids_expression = 'cache PrimaryClusterId and ReplicaClusterId "{step_key}" ' \
                                                   'SSM automation execution' \
                                                   '\n{input_parameters}'


@given(parsers.parse(cache_primary_and_replica_cluster_ids_expression))
@when(parsers.parse(cache_primary_and_replica_cluster_ids_expression))
@then(parsers.parse(cache_primary_and_replica_cluster_ids_expression))
def cache_primary_and_replica_cluster_ids(resource_pool, ssm_test_cache, boto3_session, step_key, input_parameters):
    elasticache_client = client('elasticache', boto3_session)
    replication_group_id = extract_param_value(input_parameters, 'ReplicationGroupId', resource_pool, ssm_test_cache)
    group_description = elasticache_client.describe_replication_groups(ReplicationGroupId=replication_group_id)
    node_group_members = group_description['ReplicationGroups'][0]['NodeGroups'][0]['NodeGroupMembers']
    for node_group_member in node_group_members:
        if node_group_member['CurrentRole'] == 'primary':
            put_to_ssm_test_cache(ssm_test_cache, step_key, 'PrimaryClusterId', node_group_member['CacheClusterId'])
        else:
            put_to_ssm_test_cache(ssm_test_cache, step_key, 'ReplicaClusterId', node_group_member['CacheClusterId'])
