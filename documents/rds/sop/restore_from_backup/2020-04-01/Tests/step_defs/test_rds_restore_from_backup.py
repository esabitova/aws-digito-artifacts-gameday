# coding=utf-8
import pytest
import resource_manager.src.util.ssm_utils as ssm_utils
import resource_manager.src.util.rds_util as rds_util
from pytest_bdd import (
    scenario,
)


@scenario('../features/restore_from_backup.feature', 'Restore RDS instance from backup WetRun.')
def test_restore_from_backup_wetrun():
    """Restore RDS instance from backup WetRun."""


@scenario('../features/restore_from_backup.feature', 'Restore RDS instance from backup DryRun.')
def test_restore_from_backup_dryrun():
    """Restore RDS instance from backup DryRun."""


@pytest.fixture(scope='function', autouse=True)
def tear_down_rds_backup(boto3_session, ssm_test_cache, function_logger):
    """
    TearDown SSM execution left over RDS instances after wet run scenario.
    """
    yield
    ssm_executions = ssm_test_cache.get('SsmExecutionId')
    if ssm_executions:
        ssm_execution_id = ssm_executions['1']
        step_inputs = ssm_utils.get_ssm_step_inputs(boto3_session, ssm_execution_id, 'RenamePreviousDatabaseToOld')
        if step_inputs and step_inputs.get('NewDBInstanceIdentifier'):
            instance_to_tear_down = step_inputs['NewDBInstanceIdentifier'].replace('"', '')
            rds_util.delete_db_instance(boto3_session, instance_to_tear_down, async_mode=True, logger=function_logger)
