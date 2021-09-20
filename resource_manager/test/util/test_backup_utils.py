import unittest

from botocore.exceptions import ClientError
import pytest
import logging
from unittest.mock import MagicMock, patch
import resource_manager.src.util.boto3_client_factory as client_factory
import resource_manager.src.util.backup_utils as backup_utils
from documents.util.scripts.test.test_data_provider import \
    get_sample_efs_recovery_points_by_backup_vault, \
    get_sample_recovery_points_by_backup_vault_with_efs2resource, \
    get_sample_empty_recovery_points_list, \
    get_sample_describe_backup_job, \
    get_sample_describe_recovery_point, \
    BACKUP_COMPLETED_RECOVERY_ARN, \
    BACKUP_VAULT_NAME, \
    ACCOUNT_ID
from documents.util.scripts.test.mock_sleep import MockSleep

logger = logging.getLogger(__name__)


@pytest.mark.unit_test
class TestBackupUtil(unittest.TestCase):

    def setUp(self):
        self.session_mock = MagicMock()
        self.mock_backup_service = MagicMock()
        self.client_side_effect_map = {
            'backup': self.mock_backup_service
        }
        self.session_mock.client.side_effect = lambda service_name, config=None: \
            self.client_side_effect_map.get(service_name)

    def tearDown(self):
        # Clean client factory cache after each test.
        client_factory.clients = {}
        client_factory.resources = {}

    def test_run_backup(self):
        expected_recovery_arn = f"arn:aws:backup:eu-south-1:{ACCOUNT_ID}:recovery-point:RecoveryID"

        backed_resource_arn = f"arn:aws:elasticfilesystem:eu-south-1:{ACCOUNT_ID}:file-system/fs-a40ebd61"
        backup_iam_role_arn = f"arn:aws:iam::{ACCOUNT_ID}:role/service-role/AWSBackupDefaultServiceRole"
        backup_vault_name = BACKUP_VAULT_NAME
        self.mock_backup_service.start_backup_job.return_value = \
            {
                'BackupJobId': 'TestID',
                'RecoveryPointArn': f"arn:aws:backup:eu-south-1:{ACCOUNT_ID}:recovery-point:RecoveryID",
                'CreationDate': "2021-01-01T00:00:00.000000+03:00"
            }
        self.mock_backup_service.describe_backup_job.return_value = {}
        result = backup_utils.run_backup(self.session_mock,
                                         backed_resource_arn,
                                         backup_iam_role_arn,
                                         backup_vault_name)
        self.mock_backup_service.start_backup_job.assert_called_once_with(BackupVaultName=backup_vault_name,
                                                                          IamRoleArn=backup_iam_role_arn,
                                                                          ResourceArn=backed_resource_arn
                                                                          )
        self.mock_backup_service.describe_backup_job.assert_not_called()
        self.assertEqual(result, expected_recovery_arn)

    def test_run_backup_wait(self):
        expected_recovery_arn = f"arn:aws:backup:eu-south-1:{ACCOUNT_ID}:recovery-point:RecoveryID"

        backed_resource_arn = f"arn:aws:elasticfilesystem:eu-south-1:{ACCOUNT_ID}:file-system/fs-a40ebd61"
        backup_iam_role_arn = f"arn:aws:iam::{ACCOUNT_ID}:role/service-role/AWSBackupDefaultServiceRole"
        backup_vault_name = BACKUP_VAULT_NAME
        self.mock_backup_service.start_backup_job.return_value = \
            {
                'BackupJobId': 'TestID',
                'RecoveryPointArn': f"arn:aws:backup:eu-south-1:{ACCOUNT_ID}:recovery-point:RecoveryID",
                'CreationDate': "2021-01-01T00:00:00.000000+03:00"
            }
        self.mock_backup_service.describe_backup_job.return_value = get_sample_describe_backup_job(backup_vault_name,
                                                                                                   'COMPLETED')
        result = backup_utils.run_backup(self.session_mock,
                                         backed_resource_arn,
                                         backup_iam_role_arn,
                                         backup_vault_name,
                                         wait=True,
                                         wait_timeout=1)
        self.mock_backup_service.start_backup_job.assert_called_once_with(BackupVaultName=backup_vault_name,
                                                                          IamRoleArn=backup_iam_role_arn,
                                                                          ResourceArn=backed_resource_arn
                                                                          )
        self.mock_backup_service.describe_backup_job.assert_called_with(BackupJobId='TestID')
        self.assertEqual(result, expected_recovery_arn)

    @patch('time.sleep')
    @patch('time.time')
    def test_run_backup_wait_fail(self, patched_time, patched_sleep):
        mock_sleep = MockSleep()
        patched_time.side_effect = mock_sleep.time
        patched_sleep.side_effect = mock_sleep.sleep

        backed_resource_arn = f"arn:aws:elasticfilesystem:eu-south-1:{ACCOUNT_ID}:file-system/fs-a40ebd61"
        backup_iam_role_arn = f"arn:aws:iam::{ACCOUNT_ID}:role/service-role/AWSBackupDefaultServiceRole"
        backup_vault_name = BACKUP_VAULT_NAME
        self.mock_backup_service.start_backup_job.return_value = \
            {
                'BackupJobId': 'TestID',
                'RecoveryPointArn': f"arn:aws:backup:eu-south-1:{ACCOUNT_ID}:recovery-point:RecoveryID",
                'CreationDate': "2021-01-01T00:00:00.000000+03:00"
            }
        self.mock_backup_service.describe_backup_job.return_value = get_sample_describe_backup_job(backup_vault_name,
                                                                                                   'FAILED')

        with pytest.raises(AssertionError) as assert_error:
            backup_utils.run_backup(self.session_mock,
                                    backed_resource_arn,
                                    backup_iam_role_arn,
                                    backup_vault_name,
                                    wait=True,
                                    wait_timeout=1)

        self.mock_backup_service.start_backup_job.assert_called_once_with(BackupVaultName=backup_vault_name,
                                                                          IamRoleArn=backup_iam_role_arn,
                                                                          ResourceArn=backed_resource_arn
                                                                          )
        self.mock_backup_service.describe_backup_job.assert_called_with(BackupJobId='TestID')
        logger.info(assert_error)
        self.assertEqual('Backup job TestID failed to complete, current status is FAILED', str(assert_error.value))

    def test_get_recovery_point(self):
        backup_vault_name = BACKUP_VAULT_NAME
        self.mock_backup_service. \
            list_recovery_points_by_backup_vault. \
            return_value = get_sample_efs_recovery_points_by_backup_vault(backup_vault_name)
        result = backup_utils.get_recovery_point(self.session_mock, backup_vault_name, 'EFS')
        self.mock_backup_service.list_recovery_points_by_backup_vault. \
            assert_called_once_with(BackupVaultName=backup_vault_name,
                                    ByResourceType='EFS')
        self.assertEqual(result, BACKUP_COMPLETED_RECOVERY_ARN)

    def test_get_recovery_point_failed(self):
        backup_vault_name = BACKUP_VAULT_NAME
        resource_type = 'EFS'
        self.mock_backup_service. \
            list_recovery_points_by_backup_vault. \
            return_value = get_sample_empty_recovery_points_list()
        with pytest.raises(AttributeError) as attr_error:
            backup_utils.get_recovery_point(self.session_mock, backup_vault_name, resource_type)
        self.mock_backup_service.list_recovery_points_by_backup_vault. \
            assert_called_once_with(BackupVaultName=backup_vault_name,
                                    ByResourceType=resource_type)
        self.assertEqual(f'No recovery points found for {resource_type} in {BACKUP_VAULT_NAME}', str(attr_error.value))

    def test_get_recovery_points(self):
        backup_vault_name = BACKUP_VAULT_NAME
        self.mock_backup_service. \
            list_recovery_points_by_backup_vault. \
            return_value = get_sample_efs_recovery_points_by_backup_vault(backup_vault_name)
        result = backup_utils.get_recovery_points(self.session_mock, backup_vault_name)
        self.mock_backup_service.list_recovery_points_by_backup_vault. \
            assert_called_once_with(BackupVaultName=backup_vault_name)
        self.assertEqual(result, get_sample_efs_recovery_points_by_backup_vault(backup_vault_name)['RecoveryPoints'])

    def test_get_recovery_points_by_resource_type(self):
        backup_vault_name = BACKUP_VAULT_NAME
        resource_type = 'EFS2'
        self.mock_backup_service. \
            list_recovery_points_by_backup_vault. \
            return_value = {'RecoveryPoints': [x for x in
                                               get_sample_efs_recovery_points_by_backup_vault(backup_vault_name)[
                                                   'RecoveryPoints']
                                               if x['ResourceType'] == resource_type]}
        result = backup_utils.get_recovery_points(self.session_mock, backup_vault_name, resource_type=resource_type)
        self.mock_backup_service.list_recovery_points_by_backup_vault. \
            assert_called_once_with(BackupVaultName=backup_vault_name, ByResourceType=resource_type)
        self.assertEqual(result,
                         get_sample_recovery_points_by_backup_vault_with_efs2resource(backup_vault_name)
                         ['RecoveryPoints'])

    def test_get_recovery_points_with_wrong_resource_arn(self):
        backup_vault_name = BACKUP_VAULT_NAME
        self.mock_backup_service. \
            list_recovery_points_by_backup_vault. \
            return_value = get_sample_empty_recovery_points_list()
        result = backup_utils.get_recovery_points(self.session_mock, backup_vault_name, resource_arn='test')
        self.mock_backup_service.list_recovery_points_by_backup_vault. \
            assert_called_once_with(BackupVaultName=backup_vault_name, ByResourceArn='test')
        self.assertEqual(result, [])

    def test_delete_backup_vault(self):
        backup_vault_name = BACKUP_VAULT_NAME
        self.mock_backup_service. \
            delete_backup_vault. \
            return_value = None
        backup_utils.delete_backup_vault(self.session_mock, backup_vault_name)
        self.mock_backup_service.delete_backup_vault. \
            assert_called_once_with(BackupVaultName=backup_vault_name)

    def test_delete_backup_vault_in_region(self):
        backup_vault_name = BACKUP_VAULT_NAME
        region = 'eu-west-1'
        self.mock_backup_service. \
            delete_backup_vault. \
            return_value = None
        self.session_mock.client.side_effect = lambda service_name, region_name=region: \
            self.client_side_effect_map.get(service_name)
        backup_utils.delete_backup_vault(self.session_mock, backup_vault_name, region=region)
        self.session_mock.client. \
            assert_called_once_with('backup', region_name=region)
        self.mock_backup_service.delete_backup_vault. \
            assert_called_once_with(BackupVaultName=backup_vault_name)

    def test_delete_recovery_point(self):
        backup_vault_name = BACKUP_VAULT_NAME
        recovery_point_arn = BACKUP_COMPLETED_RECOVERY_ARN
        self.mock_backup_service. \
            delete_recovery_point. \
            return_value = None
        backup_utils.delete_recovery_point(self.session_mock,
                                           backup_vault_name=backup_vault_name,
                                           recovery_point_arn=recovery_point_arn)
        self.mock_backup_service.delete_recovery_point. \
            assert_called_once_with(BackupVaultName=backup_vault_name, RecoveryPointArn=recovery_point_arn)

    def test_delete_recovery_point_in_region(self):
        backup_vault_name = BACKUP_VAULT_NAME
        recovery_point_arn = BACKUP_COMPLETED_RECOVERY_ARN
        region = 'eu-west-1'
        self.mock_backup_service. \
            delete_recovery_point. \
            return_value = None
        self.session_mock.client.side_effect = lambda service_name, region_name=region: \
            self.client_side_effect_map.get(service_name)
        backup_utils.delete_recovery_point(self.session_mock,
                                           backup_vault_name=backup_vault_name,
                                           recovery_point_arn=recovery_point_arn,
                                           region=region)
        self.mock_backup_service.delete_recovery_point. \
            assert_called_once_with(BackupVaultName=backup_vault_name, RecoveryPointArn=recovery_point_arn)

    def test_delete_recovery_point_wait(self):
        backup_vault_name = BACKUP_VAULT_NAME
        recovery_point_arn = BACKUP_COMPLETED_RECOVERY_ARN
        self.mock_backup_service. \
            delete_recovery_point. \
            return_value = None
        self.mock_backup_service.describe_recovery_point.side_effect = ClientError(
            error_response={"Error": {"Code": "ResourceNotFound"}},
            operation_name='DescribeRecoveryPoint'
        )

        backup_utils.delete_recovery_point(self.session_mock,
                                           backup_vault_name=backup_vault_name,
                                           recovery_point_arn=recovery_point_arn,
                                           wait=True,
                                           wait_timeout=1)
        self.mock_backup_service.delete_recovery_point. \
            assert_called_once_with(BackupVaultName=backup_vault_name, RecoveryPointArn=recovery_point_arn)

    @patch('time.sleep')
    @patch('time.time')
    def test_delete_recovery_point_wait_fail(self, patched_time, patched_sleep):
        mock_sleep = MockSleep()
        patched_time.side_effect = mock_sleep.time
        patched_sleep.side_effect = mock_sleep.sleep

        backup_vault_name = BACKUP_VAULT_NAME
        recovery_point_arn = BACKUP_COMPLETED_RECOVERY_ARN
        self.mock_backup_service. \
            delete_recovery_point. \
            return_value = None
        self.mock_backup_service.describe_recovery_point.return_value = \
            get_sample_describe_recovery_point(backup_vault_name)
        with pytest.raises(TimeoutError) as timeout_error:
            backup_utils.delete_recovery_point(self.session_mock,
                                               backup_vault_name=backup_vault_name,
                                               recovery_point_arn=recovery_point_arn,
                                               wait=True,
                                               wait_timeout=1)
        self.mock_backup_service.delete_recovery_point. \
            assert_called_once_with(BackupVaultName=backup_vault_name, RecoveryPointArn=recovery_point_arn)
        self.assertEqual(
            f'Recovery point \'{BACKUP_COMPLETED_RECOVERY_ARN.split(":")[-1]}\' wasn\'t removed during timeout',
            str(timeout_error.value)
        )

    def test_issue_a_backup_job_and_immediately_abort_it(self):
        backup_vault_name = BACKUP_VAULT_NAME
        backup_iam_role_arn = f"arn:aws:iam::{ACCOUNT_ID}:role/service-role/AWSBackupDefaultServiceRole"
        backup_vault_name = BACKUP_VAULT_NAME
        backed_resource_arn = f"arn:aws:elasticfilesystem:eu-south-1:{ACCOUNT_ID}:file-system/fs-a40ebd61"

        self.mock_backup_service.start_backup_job.return_value = \
            {
                'BackupJobId': 'TestID',
                'RecoveryPointArn': f"arn:aws:backup:eu-south-1:{ACCOUNT_ID}:recovery-point:RecoveryID",
                'CreationDate': "2021-01-01T00:00:00.000000+03:00"
            }

        backup_utils.issue_a_backup_job_and_immediately_abort_it(self.session_mock,
                                                                 backed_resource_arn,
                                                                 backup_iam_role_arn,
                                                                 backup_vault_name
                                                                 )
        self.mock_backup_service.start_backup_job.assert_called_once_with(BackupVaultName=backup_vault_name,
                                                                          IamRoleArn=backup_iam_role_arn,
                                                                          ResourceArn=backed_resource_arn
                                                                          )

        self.mock_backup_service.stop_backup_job.assert_called_once_with(BackupJobId='TestID')
