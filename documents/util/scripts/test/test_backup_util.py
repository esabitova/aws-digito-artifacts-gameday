import unittest
import pytest
import documents.util.scripts.src.backup_util as backup_util

from botocore.exceptions import ClientError
from unittest.mock import patch, MagicMock
from documents.util.scripts.test.mock_sleep import MockSleep


@pytest.mark.unit_test
class TestBackupUtil(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('boto3.client')
        self.client = self.patcher.start()
        self.mock_backup = MagicMock()
        self.side_effect_map = {
            'backup': self.mock_backup
        }
        self.client.side_effect = lambda service_name, config=None: self.side_effect_map.get(service_name)

    def tearDown(self):
        self.patcher.stop()

    def test_copy_backup_in_region_wrong_events(self):
        events = {
            'IamRoleArn': 'test',
            'RecoveryPointArn': 'test',
            'IdempotencyToken': 'test',
            'DestinationBackupVaultArn': 'test'
        }
        with pytest.raises(KeyError) as key_error:
            backup_util.copy_backup_in_region(events, None)
        self.mock_backup.start_copy_job.assert_not_called()
        self.assertEqual('Requires SourceBackupVaultName in events', str(key_error.value).strip('"').strip('\''))

    def test_copy_backup_in_region(self):
        events = {
            'IamRoleArn': 'test',
            'RecoveryPointArn': 'test',
            'IdempotencyToken': 'test',
            'DestinationBackupVaultArn': 'test',
            'SourceBackupVaultName': 'test'
        }
        self.mock_backup.start_copy_job.return_value = {
            'CopyJobId': 'F45BBF9B-B18D-6831-62BA-59C12037613D',
            'CreationDate': '2021-05-04T13:19:51.757000+03:00'
        }
        response = backup_util.copy_backup_in_region(events, None)
        self.mock_backup.start_copy_job.assert_called_once_with(
            RecoveryPointArn=events['RecoveryPointArn'],
            SourceBackupVaultName=events['SourceBackupVaultName'],
            DestinationBackupVaultArn=events['DestinationBackupVaultArn'],
            IamRoleArn=events['IamRoleArn'],
            IdempotencyToken=events['IdempotencyToken']
        )
        self.assertEqual(response, {'CopyJobId': 'F45BBF9B-B18D-6831-62BA-59C12037613D'})

    def test_copy_backup_in_region_wrong_recovery_arn(self):
        events = {
            'IamRoleArn': 'test',
            'RecoveryPointArn': 'test',
            'IdempotencyToken': 'test',
            'DestinationBackupVaultArn': 'test',
            'SourceBackupVaultName': 'test'
        }
        self.mock_backup.start_copy_job.side_effect = ClientError(
            error_response={"Error": {"Code": "ResourceNotFound"}},
            operation_name='StartCopyJob'
        )
        with pytest.raises(ClientError) as key_error:
            backup_util.copy_backup_in_region(events, None)
        assert 'An error occurred (ResourceNotFound)' in str(key_error.value)

    def test_restore_backup_in_region_wrong_events(self):
        events = {
            'RecoveryPointArn': 'test',
            'IdempotencyToken': 'test',
            'DestinationBackupVaultArn': 'test',
            'Metadata': {},
            'Region': 'test',
            'ResourceType': 'test'
        }
        with pytest.raises(KeyError) as key_error:
            backup_util.restore_backup_in_region(events, None)
        self.mock_backup.start_restore_job.assert_not_called()
        self.assertEqual('Requires IamRoleArn in events', str(key_error.value).strip('"').strip('\''))

    def test_restore_backup_in_region_wrong_metadata(self):
        region = 'eu-west-1'
        events = {
            'IamRoleArn': 'test',
            'RecoveryPointArn': 'test',
            'IdempotencyToken': 'test',
            'DestinationBackupVaultArn': 'test',
            'Metadata': {
                'Encrypted': 'False',
                'PerformanceMode': 'generalPurpose',
                'newFileSystem': 'True',
                'CreationToken': 'test'
            },
            'Region': 'test',
            'ResourceType': 'test'
        }
        self.client.side_effect = lambda service_name, region_name=region: \
            self.side_effect_map.get(service_name)
        with pytest.raises(KeyError) as key_error:
            backup_util.restore_backup_in_region(events, None)
        self.mock_backup.start_restore_job.assert_not_called()
        self.assertEqual('Requires file-system-id in events\' Metadata', str(key_error.value).strip('"').strip('\''))

    def test_restore_backup_in_region(self):
        region = 'eu-west-1'
        events = {
            'IamRoleArn': 'test',
            'RecoveryPointArn': 'test',
            'IdempotencyToken': 'test',
            'DestinationBackupVaultArn': 'test',
            'Metadata': {
                'file-system-id': 'fs-test',
                'Encrypted': 'False',
                'PerformanceMode': 'generalPurpose',
                'newFileSystem': 'True',
                'CreationToken': 'test'
            },
            'Region': 'test',
            'ResourceType': 'test'
        }
        self.client.side_effect = lambda service_name, region_name=region: \
            self.side_effect_map.get(service_name)
        self.mock_backup.start_restore_job.return_value = {
            'RestoreJobId': 'F45BBF9B-B18D-6831-62BA-59C12037613D',
            'CreationDate': '2021-05-04T13:19:51.757000+03:00'
        }
        response = backup_util.restore_backup_in_region(events, None)
        self.mock_backup.start_restore_job.assert_called_once_with(
            RecoveryPointArn=events['RecoveryPointArn'],
            Metadata={
                'file-system-id': events['Metadata']['file-system-id'],
                'Encrypted': events['Metadata']['Encrypted'],
                'PerformanceMode': events['Metadata']['PerformanceMode'],
                'CreationToken': events['Metadata']['CreationToken'],
                'newFileSystem': events['Metadata']['newFileSystem']
            },
            IamRoleArn=events['IamRoleArn'],
            IdempotencyToken=events['IdempotencyToken'],
            ResourceType=events['ResourceType'],
        )
        self.assertEqual(response, {'RestoreJobId': 'F45BBF9B-B18D-6831-62BA-59C12037613D'})

    def test_restore_backup_in_region_wrong_recovery_point_arn(self):
        region = 'eu-west-1'
        events = {
            'IamRoleArn': 'test',
            'RecoveryPointArn': 'test',
            'IdempotencyToken': 'test',
            'DestinationBackupVaultArn': 'test',
            'Metadata': {
                'file-system-id': 'fs-test',
                'Encrypted': 'False',
                'PerformanceMode': 'generalPurpose',
                'newFileSystem': 'True',
                'CreationToken': 'test'
            },
            'Region': 'test',
            'ResourceType': 'test'
        }
        self.client.side_effect = lambda service_name, region_name=region: \
            self.side_effect_map.get(service_name)
        self.mock_backup.start_restore_job.side_effect = ClientError(
            error_response={"Error": {"Code": "ResourceNotFound"}},
            operation_name='StartCopyJob'
        )
        with pytest.raises(ClientError) as key_error:
            backup_util.restore_backup_in_region(events, None)
        assert 'An error occurred (ResourceNotFound)' in str(key_error.value)

    def test_wait_restore_job_in_region_wrong_events(self):
        events = {
            'RestoreJobId': 'test',

        }
        with pytest.raises(KeyError) as key_error:
            backup_util.wait_restore_job_in_region(events, None)
        self.mock_backup.describe_restore_job.assert_not_called()
        self.assertEqual('Requires Region in events', str(key_error.value).strip('"').strip('\''))

    def test_wait_restore_job_in_region(self):
        region = 'eu-west-1'
        events = {
            'Region': region,
            'RestoreJobId': 'F45BBF9B-B18D-6831-62BA-59C12037613D'
        }
        self.client.side_effect = lambda service_name, region_name=region: \
            self.side_effect_map.get(service_name)
        self.mock_backup.describe_restore_job.return_value = {
            'RestoreJobId': 'F45BBF9B-B18D-6831-62BA-59C12037613D',
            'CreationDate': '2021-05-04T13:19:51.757000+03:00',
            'Status': 'COMPLETED',
            'CreatedResourceArn': 'testResourceArn'
        }
        response = backup_util.wait_restore_job_in_region(events, None)
        self.mock_backup.describe_restore_job.assert_called_with(
            RestoreJobId=events['RestoreJobId']
        )
        self.assertEqual(response, {
            'RestoreJobId': 'F45BBF9B-B18D-6831-62BA-59C12037613D',
            'CreatedResourceArn': 'testResourceArn'
        })

    def test_wait_restore_job_in_region_failed(self):
        region = 'eu-west-1'
        events = {
            'Region': region,
            'RestoreJobId': 'F45BBF9B-B18D-6831-62BA-59C12037613D'
        }
        self.client.side_effect = lambda service_name, region_name=region: \
            self.side_effect_map.get(service_name)
        self.mock_backup.describe_restore_job.return_value = {
            'RestoreJobId': 'F45BBF9B-B18D-6831-62BA-59C12037613D',
            'CreationDate': '2021-05-04T13:19:51.757000+03:00',
            'Status': 'FAILED'
        }
        with pytest.raises(AssertionError) as assertion_error:
            backup_util.wait_restore_job_in_region(events, None)
        self.mock_backup.describe_restore_job.assert_called_with(
            RestoreJobId=events['RestoreJobId']
        )
        self.assertEqual("Restore job resulted with FAILED status", str(assertion_error.value))

    @patch('time.sleep')
    @patch('time.time')
    def test_wait_restore_job_in_region_timeout(self, patched_time, patched_sleep):
        mock_sleep = MockSleep()
        patched_time.side_effect = mock_sleep.time
        patched_sleep.side_effect = mock_sleep.sleep
        wait_timeout = 10
        region = 'eu-west-1'
        events = {
            'Region': region,
            'RestoreJobId': 'F45BBF9B-B18D-6831-62BA-59C12037613D',
            'WaitTimeout': wait_timeout
        }
        self.client.side_effect = lambda service_name, region_name=region: \
            self.side_effect_map.get(service_name)
        self.mock_backup.describe_restore_job.return_value = {
            'RestoreJobId': 'F45BBF9B-B18D-6831-62BA-59C12037613D',
            'CreationDate': '2021-05-04T13:19:51.757000+03:00',
            'Status': 'RUNNING'
        }
        with pytest.raises(TimeoutError) as timeout_error:
            backup_util.wait_restore_job_in_region(events, None)
        self.mock_backup.describe_restore_job.assert_called_with(
            RestoreJobId=events['RestoreJobId']
        )
        self.assertEqual(f"Restore job couldn't be completed within {wait_timeout} seconds", str(timeout_error.value))
