import logging

from pytest_bdd import parsers, given
import pytest
import resource_manager.src.util.common_test_utils as common_test_utils

from resource_manager.src.util import ecs_utils


@given(parsers.parse('create new task definition and cache it as "{cache_property}" '
                     '"{step_key}" SSM automation execution\n{input_parameters}'))
def create_new_task_def(ssm_test_cache,
                        resource_pool,
                        boto3_session,
                        cache_property,
                        step_key,
                        input_parameters,
                        ecs_delete_task_definition):
    old_td_arn = common_test_utils.extract_param_value(input_parameters, 'TaskDefinitionArn',
                                                       resource_pool, ssm_test_cache)
    service_name = common_test_utils.extract_param_value(input_parameters, 'ServiceName',
                                                         resource_pool, ssm_test_cache)
    cluster_name = common_test_utils.extract_param_value(input_parameters, 'ClusterName',
                                                         resource_pool, ssm_test_cache)
    new_td_arn = ecs_utils.create_new_task_def(old_td_arn, boto3_session)
    # Prepare teardown

    ecs_delete_task_definition['td_arn'] = new_td_arn
    ecs_delete_task_definition['old_td_arn'] = old_td_arn
    ecs_delete_task_definition['service_name'] = service_name
    ecs_delete_task_definition['cluster_name'] = cluster_name
    ecs_delete_task_definition['wait_sec'] = 180
    ecs_delete_task_definition['delay_sec'] = 15
    logging.info(f'Created Task Definition with arn:{new_td_arn}')
    common_test_utils.put_to_ssm_test_cache(ssm_test_cache, step_key,
                                            cache_property, new_td_arn)


@pytest.fixture(scope='function')
def ecs_delete_task_definition(boto3_session):
    task_definition_dict = {}
    yield task_definition_dict

    ecs_utils.delete_task_definition(task_definition_dict['td_arn'],
                                     task_definition_dict['service_name'],
                                     task_definition_dict['cluster_name'],
                                     task_definition_dict['old_td_arn'],
                                     task_definition_dict['wait_sec'],
                                     task_definition_dict['delay_sec'],
                                     boto3_session)
