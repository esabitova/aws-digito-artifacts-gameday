# coding=utf-8
import pytest
import datetime
import resource_manager.src.util.ssm_utils as ssm_utils
import resource_manager.src.util.rds_util as rds_util
from pytest_bdd import (
    scenario,
)
from resource_manager.src.util.boto3_client_factory import client


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

        # Removing db instance left after SSM execution in case of wet testing.
        step_inputs = ssm_utils.get_ssm_step_inputs(boto3_session, ssm_execution_id, 'RenamePreviousDatabaseToOld')
        if step_inputs and step_inputs.get('NewDBInstanceIdentifier'):
            instance_to_tear_down = step_inputs['NewDBInstanceIdentifier'].replace('"', '')
            rds_util.delete_db_instance(boto3_session, instance_to_tear_down, async_mode=True, logger=function_logger)

        # Creating db instance snapshot after SSM execution if missing.
        ssm_client = client('ssm', boto3_session)
        ssm_response = ssm_client.get_automation_execution(AutomationExecutionId=ssm_execution_id)
        db_instance_id = ssm_response['AutomationExecution']['Parameters']['DbInstanceIdentifier'][0]
        rds_client = client('rds', boto3_session)
        response = rds_client.describe_db_snapshots(DBInstanceIdentifier=db_instance_id)
        if len(response['DBSnapshots']) < 1:
            utc_time_now = datetime.datetime.utcnow()
            db_snapshot_name = db_instance_id + '-' + utc_time_now.strftime("%d-%m-%Y-%H-%M-%S-integ-test")
            rds_util.create_db_snapshot(boto3_session, db_instance_id, db_snapshot_name,
                                        async_mode=True, logger=function_logger)
