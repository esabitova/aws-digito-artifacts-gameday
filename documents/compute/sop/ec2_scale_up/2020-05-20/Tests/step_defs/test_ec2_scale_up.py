# coding=utf-8
import pytest
from pytest_bdd import (
    scenario,
    given,
)
from pytest_bdd.parsers import parse
from resource_manager.src.util.param_utils import parse_param_values_from_table
from resource_manager.src.util.ec2_utils import modify_ec2_instance_type


@scenario('../features/ec2_scale_up_usual_case.feature',
          'Execute SSM automation document Digito-Ec2ScaleUp_2020-05-20 and '
          'without instance type override')
def test_ec2_scale_up_usual_case():
    """Execute SSM automation document Digito-Ec2ScaleUp_2020-05-20"""


@scenario('../features/ec2_scale_up_usual_case.feature',
          'Execute SSM automation document Digito-Ec2ScaleUp_2020-05-20 and '
          'with instance type override')
def test_ec2_scale_up_override_type_case():
    """Execute SSM automation document Digito-Ec2ScaleUp_2020-05-20 with instance type override"""


@given(parse('cached EC2 instance id\n{input_params}'))
def cache_ec2_instance_id(input_params, cfn_output_params, ssm_test_cache, function_logger):
    params = parse_param_values_from_table(input_params, {'cfn-output': cfn_output_params})
    instance_id = params[0].get('InstanceId')
    function_logger.info(f'Caching EC2 [InstanceId] with value [{instance_id}].')
    ssm_test_cache['InstanceId'] = instance_id


@pytest.fixture(scope='function', autouse=True)
def tear_down_ec2_scale_up(boto3_session, ssm_test_cache, resource_pool, function_logger):
    """
    Tear down for EC2 scale up integration test to revert EC2 instance type back to original after scale up.
    :param boto3_session: The boto3 session.
    :param ssm_test_cache: The cache.
    :param resource_pool: The resource pool (used only to trick order of resource release to the pool,
    so that resources released after tear down)
    :param function_logger: The logger.
    """
    yield
    instance_type = ssm_test_cache.get('InstanceType')
    instance_id = ssm_test_cache.get('InstanceId')
    function_logger.info(f'Reverting EC2 instance [{instance_id}] type to [{instance_type}] after scale up.')
    modify_ec2_instance_type(boto3_session, instance_id, instance_type, function_logger)
