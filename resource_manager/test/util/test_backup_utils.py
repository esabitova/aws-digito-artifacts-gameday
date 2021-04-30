import unittest
import pytest
from unittest.mock import MagicMock
import resource_manager.src.util.boto3_client_factory as client_factory
import resource_manager.src.util.backup_utils as backup_utils
from documents.util.scripts.test.test_data_provider import \
    get_sample_efs_recovery_points_by_backup_vault, \
    get_sample_empty_recovery_points_list, \
    BACKUP_COMPLETED_RECOVERY_ARN, \
    BACKUP_VAULT_NAME, \
    ACCOUNT_ID


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

    def test_get_recovery_point(self):
        backup_vault_name = BACKUP_VAULT_NAME
        self.mock_backup_service.\
            list_recovery_points_by_backup_vault.\
            return_value = get_sample_efs_recovery_points_by_backup_vault(backup_vault_name)
        result = backup_utils.get_recovery_point(self.session_mock, backup_vault_name, 'EFS')
        self.mock_backup_service.list_recovery_points_by_backup_vault.\
            assert_called_once_with(BackupVaultName=backup_vault_name,
                                    ByResourceType='EFS')
        self.assertEqual(result, BACKUP_COMPLETED_RECOVERY_ARN)

    def test_get_recovery_points(self):
        backup_vault_name = BACKUP_VAULT_NAME
        self.mock_backup_service. \
            list_recovery_points_by_backup_vault. \
            return_value = get_sample_efs_recovery_points_by_backup_vault(backup_vault_name)
        result = backup_utils.get_recovery_points(self.session_mock, backup_vault_name)
        self.mock_backup_service.list_recovery_points_by_backup_vault. \
            assert_called_once_with(BackupVaultName=backup_vault_name)
        self.assertEqual(result, get_sample_efs_recovery_points_by_backup_vault(backup_vault_name)['RecoveryPoints'])

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
        # not getting except ???
        self.mock_backup_service.delete_backup_vault. \
            assert_called_once_with(BackupVaultName=backup_vault_name)

    # def test_delete_recovery_point(self):
    #     backup_vault_name = BACKUP_VAULT_NAME
    #     recovery_point_arn = BACKUP_COMPLETED_RECOVERY_ARN
    #     self.mock_backup_service. \
    #         delete_recovery_point. \
    #         return_value = None
    #     backup_utils.delete_recovery_point(self.session_mock, backup_vault_name)
    #     self.mock_backup_service.delete_recovery_point. \
    #         assert_called_once_with(BackupVaultName=backup_vault_name)
