BACKUP_PENDING_RECOVERY_ARN = "arn:aws:backup:eu-south-1:000000031337:recovery-point:TestPending"
BACKUP_COMPLETED_RECOVERY_ARN = "arn:aws:backup:eu-south-1:000000031337:recovery-point:TestCompleted"
BACKUP_VAULT_NAME = "test-backup-vault"


def list_empty_recovery_points():
    return {
        "RecoveryPoints": []
    }


def list_efs_recovery_points_by_backup_vault(backup_vault_name):
    return {
        "RecoveryPoints": [
            {
                "RecoveryPointArn": BACKUP_PENDING_RECOVERY_ARN,
                "backup_vault_name": backup_vault_name,
                "BackupVaultArn": "arn:aws:backup:eu-south-1:000000031337:backup-vault:" + backup_vault_name,
                "ResourceArn": "arn:aws:elasticfilesystem:eu-south-1:000000031337:file-system/fs-fb67d43e",
                "ResourceType": "EFS",
                "IamRoleArn": "arn:aws:iam::000000031337:role/service-role/AWSBackupDefaultServiceRole",
                "Status": "PENDING",
                "CreationDate": "2021-04-16T10:55:24.093000+03:00",
                "CompletionDate": "2021-04-16T10:55:31.997000+03:00",
                "BackupSizeInBytes": 0,
                "EncryptionKeyArn": "arn:aws:kms:eu-south-1:000000031337:key/TestKeyId",
                "IsEncrypted": True,
                "LastRestoreTime": "2021-04-16T11:05:59.952000+03:00"
            },
            {
                "RecoveryPointArn": BACKUP_COMPLETED_RECOVERY_ARN,
                "backup_vault_name": backup_vault_name,
                "BackupVaultArn": "arn:aws:backup:eu-south-1:000000031337:backup-vault:" + backup_vault_name,
                "ResourceArn": "arn:aws:elasticfilesystem:eu-south-1:000000031337:file-system/fs-fb67d43e",
                "ResourceType": "EFS",
                "IamRoleArn": "arn:aws:iam::000000031337:role/service-role/AWSBackupDefaultServiceRole",
                "Status": "COMPLETED",
                "CreationDate": "2021-04-16T10:47:48.679000+03:00",
                "CompletionDate": "2021-04-16T10:47:55.851000+03:00",
                "BackupSizeInBytes": 0,
                "EncryptionKeyArn": "arn:aws:kms:eu-south-1:000000031337:key/TestKeyId",
                "IsEncrypted": True
            }
        ]
    }
