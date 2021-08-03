import logging

import pytest
from pytest_bdd import (
    when,
    given,
    parsers
)

from resource_manager.src.util import boto3_client_factory
from resource_manager.src.util.param_utils import parse_param_value

logger = logging.getLogger(__name__)


@given(parsers.parse('set target group "{target_group_arn}" healthcheck port "{healthcheck_port}"'))
@when(parsers.parse('set target group "{target_group_arn}" healthcheck port "{healthcheck_port}"'))
def break_targets_healthcheck_port(boto3_session, resource_pool, cfn_output_params,
                                   ssm_test_cache, target_group_arn, healthcheck_port,
                                   break_targets_healthcheck_port_teardown):
    target_group_arn = parse_param_value(target_group_arn, {'cache': ssm_test_cache, 'cfn-output': cfn_output_params})
    healthcheck_port = parse_param_value(healthcheck_port, {'cache': ssm_test_cache, 'cfn-output': cfn_output_params})

    elb_client = boto3_client_factory.client('elbv2', boto3_session)
    describe_response = elb_client.describe_target_groups(TargetGroupArns=[target_group_arn])

    target_group = describe_response.get('TargetGroups')[0]
    break_targets_healthcheck_port_teardown['previous_healthcheck_port'] = target_group.get('HealthCheckPort')
    break_targets_healthcheck_port_teardown['target_group_arn'] = target_group_arn

    logger.info(f"HealthCheckPort = {break_targets_healthcheck_port_teardown['previous_healthcheck_port']}")
    logger.info(f"Сhange healthcheck port to {healthcheck_port}")
    elb_client.modify_target_group(
        TargetGroupArn=target_group_arn,
        HealthCheckPort=str(healthcheck_port)
    )


@pytest.fixture(scope='function')
def break_targets_healthcheck_port_teardown(boto3_session):
    teardown_dict = {}
    yield teardown_dict

    previous_healthcheck_port = teardown_dict.get('previous_healthcheck_port')
    target_group_arn = teardown_dict.get('target_group_arn')

    logger.info(f"Restore healthcheck port to {previous_healthcheck_port}")
    elb_client = boto3_client_factory.client('elbv2', boto3_session)
    elb_client.modify_target_group(
        TargetGroupArn=target_group_arn,
        HealthCheckPort=str(previous_healthcheck_port)
    )
