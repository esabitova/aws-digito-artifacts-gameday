import pytest
from pytest_bdd import given, parsers

from resource_manager.src.util import param_utils
from resource_manager.src.util.common_test_utils import (extract_param_value, put_to_ssm_test_cache)


@given(parsers.parse('Create snapshot as "{step_key}" property "{cache_property}"\n{input_parameters}'))
def create_snapshot(ssm_test_cache, resource_pool, boto3_session,
                    step_key, cache_property, input_parameters, delete_snapshot):
    volume_id = extract_param_value(input_parameters, 'VolumeId', resource_pool, ssm_test_cache)
    client = boto3_session.client('ec2')
    response = client.create_snapshot(
        Description='EbsIntegTestSnapshot',
        VolumeId=volume_id)
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, response['SnapshotId'])
    ssm_test_cache['SnapshotId'] = response['SnapshotId']


@pytest.fixture(scope='function')
def delete_snapshot(ssm_test_cache, boto3_session):
    yield
    containers = {'cache': ssm_test_cache}
    snapshot_id = param_utils.parse_param_value("{{cache:SnapshotId}}", containers)
    client = boto3_session.client('ec2')
    client.delete_snapshot(SnapshotId=snapshot_id)
