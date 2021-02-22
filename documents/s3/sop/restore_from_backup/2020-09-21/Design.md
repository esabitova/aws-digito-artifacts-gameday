# Id

s3:sop:restore_from_backup:2020-09-21

## Intent

To restore an S3 bucket from a backup bucket

## Type

Region Outage SOP

## Risk

Small

## Requirements

* The backup bucket exists to restore files from it to the target bucket
* The target bucket exists

## Permission required for AutomationAssumeRole

* s3:PutObject
* s3:GetObject
* s3:ListBucket

## Supports Rollback

Yes

## Inputs

### `S3BackupBucketName`

* Description: (Required) The S3 backup bucket name to copy files from it to the S3 restore bucket.
* Type: String

### `S3BucketToRestoreName`

* Description: (Required) The S3 bucket name to restore files from the S3 backup bucket.
* Type: String

### `AutomationAssumeRole`:

* Description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf. See Permissions required above for test.
* Type: String

### `SNSTopicARNForManualApproval`:

* Description: (Required) The ARN of the SNS Topic where a user will receive the notification about the manual approval of restore bucket clean-up if some files exist there.
* Type: String

### `UserWhoWillApproveCleanUpOfRestoreBucket`:

* Description: (Required) ARN of AWS authenticated principal who are able to either approve or reject the clean-up of restore bucket if there are some files. Can be either an AWS Identity and Access
  Management (IAM) user name or IAM user ARN or IAM role ARN or IAM assume role user ARN
* Type: String

## Details of SSM Document steps:

1. `CheckExistenceOfObjectsInRestoreBucket`
    * Type: aws:executeScript
    * Inputs:
        * `S3BucketToRestoreName`
    * Outputs:
        * `AreObjectsExistInRestoreBucket`: It is true if `S3BucketToRestoreName` has at least one versioned or non-versioned object as well as at least one delete marker
        * `NumberOfObjectsExistInRestoreBucket`: The number of files in `S3BucketToRestoreName` if they exist there
    * Explanation:
        * Call [list_object_versions](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.list_object_versions) to check if even some versions of
          objects (`.Versions` field in response) or delete markers (`.DeleteMarkers` field in response) exist as well as objects too
        * Return status of existence
1. `ApproveOrRestoreBranch`
    * Type: aws:branch
    * Inputs:
        * `CheckExistenceOfObjectsInRestoreBucket.AreObjectsExistInRestoreBucket`
    * Outputs: none
    * Explanation:
        * If `CheckExistenceOfObjectsInRestoreBucket.AreObjectsExistInRestoreBucket` is true, go to the step `ApproveCleanUpOfRestoreBucketOrCancel`. Otherwise, proceed to the step `RestoreFromBackup`
1. `ApproveCleanUpOfRestoreBucketOrCancel`
    * Type: aws:approve
    * timeoutSeconds: 3600 # one hour to wait for the approval
    * onFailure: Abort
    * Inputs:
        * `NotificationArn`: pass `SNSTopicARNForManualApproval`
        * `Message`: Do you agree to clean up the {{S3BucketToRestoreName}} bucket before the restore process? There {{NumberOfObjectsExistInRestoreBucket}} files exist.
        * `MinRequiredApprovals`: 1
        * `Approvers`: `UserWhoWillApproveCleanUpOfRestoreBucket`
    * Outputs: none
    * Explanation:
        * Ask a user to clean up of restore bucket since some files are in `S3BucketToRestoreName` bucket. If a user agree move to `CleanUpOfRestoreBucket` step. Otherwise, abort the execution.
1. `CleanUpOfRestoreBucket`
    * Type: aws:executeScript
    * Inputs:
        * `S3BucketToRestoreName`
    * Outputs:
        * `NumberOfDeletedObjects`: the number of deleted objects whether versioned file or delete marker.
    * Explanation:
        * Get list of versioned objects and delete markers by
          calling [list-object-versions](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.list-object-versions) and getting values of `.Versions`
          and `.DeleteMarkers` lists from the response
        * Delete each object in the list from the previous step by calling [delete-object](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.delete-object) in the loop
1. `RestoreFromBackup`
    * Type: aws:executeScript
    * Inputs:
        * `S3BackupBucketName`
        * `S3BucketToRestoreName`
    * Outputs:
        * `RestoredFilesNumber`: The number of successfully copied files
        * `RecoveryTimeSeconds`: The recovery time in seconds
    * Explanation:
        * Get the list of objects from the `S3BackupBucketName` bucket by
          calling [list_objects_v2](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.list_objects_v2) method
        * Copy each file in the loop one by one to the `S3BucketToRestoreName` bucket by using multipart upload in the [copy](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.copy) method and passing configured [boto3.s3.transfer.TransferConfig](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/customizations/s3.html#boto3.s3.transfer.TransferConfig)

## Outputs

* `CleanUpOfRestoreBucket.NumberOfDeletedObjects`: The number of deleted objects whether versioned file or delete marker.
* `RestoreFromBackup.RestoredFilesNumber`: The number of successfully copied files
* `RestoreFromBackup.RecoveryTimeSeconds`: The recovery time in seconds

