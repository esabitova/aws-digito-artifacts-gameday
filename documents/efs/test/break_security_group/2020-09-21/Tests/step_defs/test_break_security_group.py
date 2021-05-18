from pytest_bdd import (
    scenario,
    given,
    then,
    parsers
)

from resource_manager.src.util.common_test_utils import extract_param_value, put_to_ssm_test_cache


@scenario('../features/break_security_group.feature',
          'Create AWS resources using CloudFormation template and execute SSM automation document to '
          'test EFS behavior after breaking security group id')
def test_break_security_group():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/break_security_group_rollback.feature',
          'Create AWS resources using CloudFormation template and execute SSM automation document to '
          'test EFS behavior after breaking security group id')
def test_break_security_group_rollback():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/break_security_group_mount_targets.feature',
          'Create AWS resources using CloudFormation template and execute SSM automation document to '
          'test EFS behavior after breaking security group id')
def test_break_security_group_mount_targets():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/break_security_group_mount_targets_rollback.feature',
          'Create AWS resources using CloudFormation template and execute SSM automation document to '
          'test EFS behavior after breaking security group id')
def test_break_security_group_mount_targets_rollback():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@given(parsers.parse('cache security group id for a mount target as "{cache_property}" "{step_key}" '
                     'SSM automation execution\n{input_parameters}'))
@then(parsers.parse('cache security group id for a mount target as "{cache_property}" "{step_key}" '
                    'SSM automation execution\n{input_parameters}'))
def cache_security_group(resource_pool, boto3_session, ssm_test_cache,
                         cache_property, step_key, input_parameters):
    mt_id = extract_param_value(input_parameters, 'MountTargetId', resource_pool, ssm_test_cache)
    efs_client = boto3_session.client('efs')
    sg_list = efs_client.describe_mount_target_security_groups(
        MountTargetId=mt_id
    )['SecurityGroups']
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, sg_list)
