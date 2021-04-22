# Id

efs:sop:restore_backup_in_another_region:2020-10-26

## Intent

Restore backup in case of software failure or if it's region failure and backup replicated to another region, restore it
there

## Type

Software Outage SOP

## Risk

Medium

## Requirements

* Recovery point for EFS volume created
* IAM role with AWSBackupServiceRolePolicyForRestores policy exists

## Permission required for AutomationAssumeRole

* backup:StartRestoreJob
* backup:DescribeRestoreJob

## Supports Rollback

No.

## Inputs

### `FileSystemID`

* Description: (Required) The EFS volume ID.
* Type: String

### `RecoveryPointArn`

* Description: (Required) The Recovery Point Arn to restore.
* Type: String

### `RestoreJobIamRoleArn`

* Description: (Required) IAM role ARN with AWSBackupServiceRolePolicyForRestores policy used to restore recovery point.
* Type: String

### `Region`

* Description: (Required) Destination region, a new EFS volume will be created in that region.
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
        * `FileSystems[0].Encrypted`: Is file system encrypted
        * `FileSystems[0].KmsKeyId`: KMS key ID used to encrypt file system
        * `FileSystems[0].PerformanceMode`: The performance mode of the file system
    * Explanation:
        * Call [DescribeFileSystems](https://docs.aws.amazon.com/efs/latest/ug/API_DescribeFileSystems.html) from `efs`
        * Output filesystem's metadata to restore with the same settings
1. `RecordStartTime`
    * Type: aws:executeScript
    * Outputs:
        * `StartTime`: timestamp of the start of restore process
    * Explanation:
        * Custom script that returns current timestamp to track restore duration
1. `RestoreBackupJob`
    * Type: aws:executeScript
    * Inputs:
        * `InputPayload`:
           * `Region`: destination Region Name
           * `RecoveryPointArn`: ARN for recovery point
           * `IamRoleArn`: IAM role used to restore backup (RestoreJobIamRoleArn)
           * `IdempotencyToken`: Unique token (current datetime `{{global:DATE_TIME}}`)
           * `ResourceType`: constant string 'EFS'
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
        * Create boto3 session in region `Region`
        * Call [start_restore_job](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/backup.html#Backup.Client.start_restore_job)
          using boto3 client in target region for `backup` service to start the restore job
1. `VerifyRestoreJobStatus`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `RestoreJobId`: ID of the created restore job
    * Outputs:
        * `RecoveryPointArn`: ARN of recovered point
    * Explanation:
        * Call [DescribeRestoreJob](https://docs.aws.amazon.com/aws-backup/latest/devguide/API_DescribeRestoreJob.html)
          from `backup` service
        * Verify that the restore job has `COMPLETED` status
1. `OutputRecoveryTime`
    * Type: aws:executeScript
    * Inputs:
        * `InputPayload`:
            * `StartTime`: timestamp of the start of the restore process (RecordStartTime.StartTime)
    * Outputs:
        * `Duration`: duration of the restore process in seconds
    * Explanation:
        * Custom script that returns difference between the current timestamp and the start one

## Outputs

* `RestoreBackupJob.RestoreJobId`: ID of the restore job
* `OutputRecoveryTime.RecoveryTime`: Recovery process duration
* `VerifyRestoreJobStatus.RecoveryPointArn`: Recovery point ARN


 

