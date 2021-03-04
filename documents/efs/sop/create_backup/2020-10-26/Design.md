# Id

efs:sop:create_backup:2020-10-26

## Intent

Create a backup before major changes in configuration or a deployment

## Type

Software Outage SOP

## Risk

Low

## Requirements

* Backup vault exists to store backup
* IAM role with AWSBackupServiceRolePolicyForBackup policy exists
* All processes that write to EFS volume should be stopped before running SOP to avoid data inconsistency

## Permission required for AutomationAssumeRole

* elasticfilesystem:DescribeFileSystems
* backup:StartBackupJob
* backup:DescribeBackupJob

## Supports Rollback

No.

## Inputs

### `FileSystemID`

  * Description: (Required) The EFS ID.
  * Type: String
  
### `BackupVaultName`

  * Description: (Required) The name of a logical container where backups are stored. 
  * Type: String
  
### `BackupJobIamRoleArn`

  * Description: (Required) IAM role ARN with policy AWSBackupServiceRolePolicyForBackup used to create the target recovery point.
  * Type: String
  
### `AutomationAssumeRole`

  * Description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf.
  * Type: String

## Details of SSM Document steps

1. `GetFileSystemARN`
   * Type: aws:executeAwsApi
   * Inputs:
      * `FileSystemId`: The EFS Volume ID (FileSystemID)
   * Outputs:
      * `FileSystems[0].FileSystemArn`: ARN of the EFS volume
   * Explanation:
      * Call [DescribeFileSystems](https://docs.aws.amazon.com/efs/latest/ug/API_DescribeFileSystems.html) from `efs`
      * Output filesystem's ARN
1. `CreateBackupJob`
    * Type: aws:executeAwsApi
    * Inputs:
        * `BackupVaultName`
        * `ResourceArn`: EFS volume ARN (GetFileSystemARN.FileSystemArn)
        * `IamRoleArn`: IAM role used to create a backup (BackupJobIamRoleArn)
        * `IdempotencyToken`: Unique token (current datetime `{{global:DATE_TIME}}`)
    * Outputs:
        * `BackupJobId`: ID of the started job
        * `RecoveryPointArn`: ARN of the created recovery point
    * Explanation:
        * Call [StartBackupJob](https://docs.aws.amazon.com/aws-backup/latest/devguide/API_StartBackupJob.html) from `backup` service to create the backup job
1. `VerifyBackupJobStatus`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `BackupJobId`: ID of the created backup job
    * Explanation:
        * Call [DescribeBackupJob](https://docs.aws.amazon.com/aws-backup/latest/devguide/API_DescribeBackupJob.html) from `backup` service
        * Verify that the backup job has `COMPLETED` status        

## Outputs
  * `CreateBackupJob.RecoveryPointArn`: ARN of the created recovery point
  * `CreateBackupJob.BackupJobId`: ID of the created backup job
