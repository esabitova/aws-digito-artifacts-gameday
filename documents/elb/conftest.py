import logging
import base64
import string
import random

import pytest
from pytest_bdd import (
    when,
    given,
    parsers
)
from sttable import parse_str_table

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

    previous_healthcheck_port = teardown_dict['previous_healthcheck_port']
    target_group_arn = teardown_dict['target_group_arn']

    logger.info(f"Restore healthcheck port to {previous_healthcheck_port}")
    elb_client = boto3_client_factory.client('elbv2', boto3_session)
    elb_client.modify_target_group(
        TargetGroupArn=target_group_arn,
        HealthCheckPort=str(previous_healthcheck_port)
    )


# todo: add teardown for ssl certificate
@given(parsers.parse('self-signed ssl certificate is created and cache arn as "{certificate_arn_cache_key}"'
                     '\n{input_parameters_table}'))
@when(parsers.parse('self-signed ssl certificate is created and cache arn as "{certificate_arn_cache_key}"'
                    '\n{input_parameters_table}'))
def self_signed_ssl_certificate_is_installed(
    boto3_session, resource_pool, ssm_test_cache, certificate_arn_cache_key, input_parameters_table,
        self_signed_ssl_certificate_teardown
):
    parameters = parse_str_table(input_parameters_table, False).rows
    cert_params = {}
    for item in parameters:
        param_name = item['0']
        param_value = item['1']
        cert_params[param_name] = param_value

    unique_name = 'Digito_ALB_Test_Temporary_Certificate_' + \
                  ''.join(random.Random().choices(string.ascii_letters + string.digits, k=4))

    acm_client = boto3_session.client('acm')
    response = acm_client.import_certificate(
        Certificate=base64.b64decode(cert_params['certificate_bytes']),
        PrivateKey=base64.b64decode(cert_params['private_key_bytes']),
        Tags=[
            {
                'Key': 'Name',
                'Value': unique_name
            }
        ]
    )

    ssm_test_cache[certificate_arn_cache_key] = response['CertificateArn']
    self_signed_ssl_certificate_teardown['certificate_arn'] = response['CertificateArn']


@pytest.fixture(scope='function')
def self_signed_ssl_certificate_teardown(boto3_session):
    teardown_dict = {}
    yield teardown_dict

    acm_client = boto3_session.client('acm')

    acm_client.delete_certificate(
        CertificateArn=teardown_dict['certificate_arn']
    )
