import logging
from pytest_bdd import parsers, given, then
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


@given(parsers.parse('cache number of tasks as "{cache_property}" "{step_key}" SSM execution'
                     '\n{input_parameters}'))
@then(parsers.parse('cache number of tasks as "{cache_property}" "{step_key}" SSM execution'
                    '\n{input_parameters}'))
def cache_number_of_tasks(resource_pool, ssm_test_cache, boto3_session, cache_property, step_key,
                          input_parameters):
    ecs_cluster_name = common_test_utils.extract_param_value(input_parameters, 'ECSCluster',
                                                             resource_pool, ssm_test_cache)
    ecs_servise_name = common_test_utils.extract_param_value(input_parameters, 'ECSService',
                                                             resource_pool, ssm_test_cache)

    amount_of_task = str(ecs_utils.get_amount_of_tasks(ecs_cluster_name,
                                                       ecs_servise_name,
                                                       boto3_session))
    common_test_utils.put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, amount_of_task)


@then(parsers.parse('cache memory and cpu as "{cache_property}" "{step_key}" SSM execution'
                    '\n{input_parameters}'))
def cache_container_definitions(resource_pool, ssm_test_cache, boto3_session, cache_property, step_key,
                                input_parameters):
    ecs_task_definition = common_test_utils.extract_param_value(input_parameters, 'TaskDefinitionArn',
                                                                resource_pool, ssm_test_cache)
    container_definitions = ecs_utils.get_container_definitions(ecs_task_definition, boto3_session)
    common_test_utils.put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, container_definitions)


@then(parsers.parse('assert "{actual_property}" at "{step_key_for_actual}" '
                    'became equal to CPU and Memory'
                    '\n{input_parameters}'))
def assert_equal_cpu_and_memory(ssm_test_cache,
                                resource_pool,
                                actual_property,
                                step_key_for_actual,
                                input_parameters):
    cpu = int(common_test_utils.extract_param_value(input_parameters, 'TaskDefinitionCPU',
                                                    resource_pool, ssm_test_cache))
    memory = int(common_test_utils.extract_param_value(input_parameters, 'TaskDefinitionRAM',
                                                       resource_pool, ssm_test_cache))
    container_definitions = ssm_test_cache[step_key_for_actual][actual_property]
    assert (container_definitions["cpu"] == cpu
            and container_definitions["memory"] == memory)


@then(parsers.parse('waits until the ECSService is stable (tasks started or stopped)'
                    '\n{input_parameters}'))
def wait_services_stable(resource_pool, ssm_test_cache, boto3_session, input_parameters):
    ecs_cluster_name = common_test_utils.extract_param_value(input_parameters, 'ECSCluster',
                                                             resource_pool, ssm_test_cache)
    ecs_servise_name = common_test_utils.extract_param_value(input_parameters, 'ECSService',
                                                             resource_pool, ssm_test_cache)
    ecs_utils.wait_services_stable(ecs_cluster_name,
                                   ecs_servise_name,
                                   boto3_session)
