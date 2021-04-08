# coding=utf-8
"""SSM automation document to restore backup in another region"""

from pytest_bdd import (
    scenario,
    given,
    parsers
)

from resource_manager.src.util.backup_utils import get_recovery_point
from resource_manager.src.util.common_test_utils import extract_param_value, put_to_ssm_test_cache


@scenario('../features/restore_backup_in_another_region.feature',
          'Restore backup in another region')
def test_restore_backup():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@given(parsers.parse('cache recovery point arn as "{cache_property}"\n{input_parameters}'))
def cache_recovery_point_arn(resource_manager, ssm_test_cache, cache_property, input_parameters):
    backup_vault_name = extract_param_value(input_parameters, 'BackupVaultName', resource_manager, ssm_test_cache)

    recovery_point_arn = get_recovery_point(backup_vault_name, 'EFS')
    put_to_ssm_test_cache(ssm_test_cache, 'before', cache_property, recovery_point_arn)
