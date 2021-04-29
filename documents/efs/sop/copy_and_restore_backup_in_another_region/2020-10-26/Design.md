# Id

efs:sop:copy_and_restore_backup_in_another_region:2020-10-26

## Intent

Copy and restore backup in case of software failure or in case of region failure and backup replicated to another
region, restore it there

## Type

Software Outage SOP

## Risk

Medium

## Requirements

* Recovery point for EFS volume exists in source backup vault
* Destination backup vault exists
* IAM role with AWSBackupServiceRolePolicyForBackup policy exists
* IAM role with AWSBackupServiceRolePolicyForRestores policy exists

## Permission required for AutomationAssumeRole

* elasticfilesystem:DescribeFileSystems
* backup:ListRecoveryPointsByResource
* backup:DescribeCopyJob
* backup:StartCopyJob
* backup:StartRestoreJob

## Supports Rollback

No.

## Inputs

### `FileSystemID`

* Description: (Required) The EFS ID.
* Type: String

### `CopyJobIAMRoleArn`

* Description: (Required) IAM role ARN with AWSBackupServiceRolePolicyForBackup policy used to start the copy job.
* Type: String

### `RestoreJobIamRoleArn`

* Description: (Required) IAM role ARN with AWSBackupServiceRolePolicyForRestores policy used to start the restore job.
* Type: String

### `DestinationRegionName`

* Description: (Required) The destination region Name.
* Type: String

### `BackupVaultSourceName`

* Description: (Required) The name of the source backup vault to copy from.
* Type: String

### `RecoveryPointArn`

* Description: (Required) The Recovery Point Arn to restore.
* Type: String

### `BackupVaultDestinationArn`

* Description: (Required) The ARN of the destination backup vault to copy to.
* Type: String

### `AutomationAssumeRole`

* Description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf.
* Type: String

## Details of SSM Document steps

1. `GetFileSystemMetadata`
    * Type: aws:executeAwsApi
    * Inputs:
        * `FileSystemId`: The EFS Volume ID (FileSystemID)
    * Outputs:
        * `FileSystems[0].FileSystemArn`: ARN of the EFS volume
        * `FileSystems[0].Encrypted`: Is file system encrypted
        * `FileSystems[0].KmsKeyId`: KMS key ID used to encrypt file system
        * `FileSystems[0].PerformanceMode`: The performance mode of the file system
    * Explanation:
        * Call [DescribeFileSystems](https://docs.aws.amazon.com/efs/latest/ug/API_DescribeFileSystems.html) from `efs`
        * Output filesystem's ARN and metadata
1. `RecordStartTime`
   * Type: aws:executeScript
   * Outputs:
      * `StartTime`: timestamp of the start of copy and restore process
   * Explanation:
     * Custom script that returns current timestamp to track copy and restore duration
1. `CreateCopyJob`
    * Type: aws:executeAwsApi
    * Inputs:
        * `IamRoleArn`: IAM role used to copy a backup (CopyJobIAMRoleArn)
        * `SourceBackupVaultName`: Name of the source backup vault name (BackupVaultSourceName)
        * `DestinationBackupVaultArn`: ARN of the destination backup
          vault (`arn:aws:backup:{{DestinationRegionName}}:{{global:ACCOUNT_ID}}:backup-vault:{{BackupVaultDestinationName}}`)
        * `RecoveryPointArn`: Recovery point ARN
        * `IdempotencyToken`: Unique token (current datetime `{{global:DATE_TIME}}`)
    * Outputs:
        * `CopyJobId`: ID of the created copy job
    * Explanation:
        * Start copy job by
          calling [StartCopyJob](https://docs.aws.amazon.com/aws-backup/latest/devguide/API_StartCopyJob.html)
          from `backup` service
        * Get ID of the created job
1. `VerifyCopyJobStatus`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `CopyJobId`: ID of the created copy job
    * Explanation:
        * Call [DescribeCopyJob](https://docs.aws.amazon.com/aws-backup/latest/devguide/API_DescribeCopyJob.html)
          from `backup` service
        * Verify that the copy job has `COMPLETED` status
1. `RestoreBackupJob`
    * Type: aws:executeAwsApi
    * Inputs:
        * `RecoveryPointArn`: ARN for recovery point (DestinationRecoveryPointArn)
        * `IamRoleArn`: IAM role used to restore backup (RestoreJobIamRoleArn)
        * `IdempotencyToken`: Unique token (current datetime `{{global:DATE_TIME}}`)
        * `Metadata`:
            * `file-system-id`: EFS volume id (FileSystemID)
            * `Encrypted`: Is file system encrypted (GetFileSystemMetadata.Encrypted)
            * `KmsKeyId`: KMS key ID to encrypt file system (GetFileSystemMetadata.KmsKeyId)
            * `PerformanceMode`: Throughput mode of the file system (GetFileSystemMetadata.PerformanceMode)
            * `newFileSystem`: Restore to a new EFS volume ("true")
            * `CreationToken`: Unique token (current datetime `{{global:DATE_TIME}}`)
    * Outputs:
        * `RestoreJobId`: ID of the started job
    * Explanation:
        * Call [StartRestoreJob](https://docs.aws.amazon.com/aws-backup/latest/devguide/API_StartRestoreJob.html)
          from `backup` service to start the restore job
1. `VerifyRestoreJobStatus`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `RestoreJobId`: ID of the created restore job
    * Explanation:
        * Call [DescribeRestoreJob](https://docs.aws.amazon.com/aws-backup/latest/devguide/API_DescribeRestoreJob.html)
          from `backup` service
        * Verify that the restore job has `COMPLETED` status
1. `OutputCopyAndRestoreTime`
   * Type: aws:executeScript
   * Inputs:
      * `InputPayload`
         * `StartTime`: timestamp of the start of the restore process (RecordStartTime.StartTime)
   * Outputs:
      * `Duration`: duration of the restore process in seconds
   * Explanation:
      * Custom script that returns difference between the current timestamp and the start one

## Outputs

* `RestoreBackupJob.RestoreJobId`: ID of the restore job
* `OutputCopyAndRestoreTime.RecoveryTime`: Recovery process duration
* `GetLatestRecoveryPointARN.RecoveryPointArn`: Recovery point ARN used for recovery


 

