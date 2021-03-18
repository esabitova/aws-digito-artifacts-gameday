from pytest_bdd import (
    given,
    parsers, when
)

from resource_manager.src.util import docdb_utils as docdb_utils
from resource_manager.src.util.common_test_utils import extract_param_value, put_to_ssm_test_cache


cache_number_of_clusters_expression = 'cache current number of clusters as "{cache_property}" "{step_key}" SSM ' \
                                      'automation execution' \
                                      '\n{input_parameters}'


@given(parsers.parse(cache_number_of_clusters_expression))
@when(parsers.parse(cache_number_of_clusters_expression))
def cache_number_of_instances(
        resource_manager, ssm_test_cache, boto3_session, cache_property, step_key, input_parameters
):
    cluster_id = extract_param_value(
        input_parameters, "DBClusterIdentifier", resource_manager, ssm_test_cache
    )
    number_of_instances = docdb_utils.get_number_of_instances(boto3_session, cluster_id)
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, number_of_instances)
