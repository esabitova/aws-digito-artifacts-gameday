# Id

s3:test:accidental_delete:2020-04-01

## Intent

Accidental delete is testing the case where all versions of files in the bucket were deleted, and we are restoring from the backup bucket

## Type

Software Outage SOP

## Risk

Small

## Requirements

* S3 bucket with versioning enabled or disabled

## Permission required for AutomationAssumeRole

* s3:PutObject
* s3:GetObject
* s3:ListObjectsV2
* s3:ListObjectVersions
* s3:DeleteObject
* ssm:StartAutomationExecution
* iam:PassRole
* ssm:GetAutomationExecution
* ssm:GetParameters

Additionally, inherited from `Digito-RestoreFromBackup_2020-09-21`

* s3:ListBucket
* s3:ListBucketVersions

## Supports Rollback

Yes. The script will revert changes by copying back the deleted file from the backup bucket where it was moved temporarily. Users can run the script with `IsRollback` and `PreviousExecutionId` to roll
back changes from the previous run

## Inputs

### `S3BucketWhereObjectsWillBeDeletedFrom`:

* Description: (Required) The S3 Bucket Name where objects will be deleted.
* Type: String

### `S3BucketToRestoreWhereObjectWillBeCopiedTo`:

* Description: (Required) The S3 Bucket Name where objects will be copied.
* Type: String

### `AutomationAssumeRole`:

* Description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf. See Permissions required above for test.
* Type: String

### `S3UserErrorAlarmName`:

* type: String
* description: (Optional) Alarm which should be red after injection of the failure and green after the rollback process in the end of the test.


### `SNSTopicARNForManualApproval`:

* Description: (Required) The ARN of the SNS Topic where a user will receive the notification about the manual approval of restore bucket clean-up if some files exist there.
* Type: String

### `UserWhoWillApproveCleanRestoreBucket`:

* Description: (Required) ARN of AWS authenticated principal who are able to either approve or reject the clean-up of restore bucket if there are some files. Can be either an AWS Identity and Access
  Management (IAM) user name or IAM user ARN or IAM role ARN or IAM assume role user ARN
* Type: String

### `IsRollback`:

* type: Boolean
* description: (Optional) Run rollback step of the given previous execution (parameter `PreviousExecutionId`)
* default: False

### `PreviousExecutionId`:

* type: Integer
* description: (Optional) The id of previous execution of the current script
* default: 0

## Details of SSM Document steps:

1. `CheckIsRollback`
    * Type: aws:branch
    * Inputs:
        * `IsRollback`
    * Outputs: none
    * Explanation:
        * `IsRollback` it true, continue with `PrepareRollbackOfPreviousExecution` step
        * `IsRollback` it false, continue with `BackupS3BucketWhereObjectsWillBeDeletedFrom` step
1. `PrepareRollbackOfPreviousExecution`
    * Type: aws:executeScript
    * Inputs:
        * `PreviousExecutionId`
    * Outputs:
        * `S3BucketWhereObjectWasCopiedFrom`: The restored object
        * `S3BucketToRestoreWhereObjectWasCopiedTo`: The restored object
    * Explanation:
        * Get values of SSM Document input parameters from the previous execution using `PreviousExecutionId`:
            * `S3BucketWhereObjectWasCopiedFrom`
            * `S3BucketToRestoreWhereObjectWasCopiedTo`
1. `RollbackPreviousExecution`
    * Type: aws:executeAutomation
    * Inputs:
        * `DocumentName`: `Digito-RestoreFromBackup_2020-09-21`
        * `RuntimeParameters`:
            * `AutomationAssumeRole`: {{AutomationAssumeRole}}
            * `SNSTopicARNForManualApproval`: {{SNSTopicARNForManualApproval}}
            * `UserWhoWillApproveCleanRestoreBucket`: {{UserWhoWillApproveCleanRestoreBucket}}
            * `S3BucketToRestoreName`: {{PrepareRollbackOfPreviousExecution.S3BucketToRestoreWhereObjectWillBeCopiedTo}}
            * `S3BackupBucketName` {{PrepareRollbackOfPreviousExecution.S3BucketWhereObjectsWillBeDeletedFrom}}
    * Explanation:
        * Copy all files from the `S3BucketToRestoreWhereObjectWillBeCopiedTo` bucket to the `S3BucketWhereObjectsWillBeDeletedFrom` bucket by shared SSM Document `Digito-RestoreFromBackup_2020-09-21`
1. `BackupS3BucketWhereObjectsWillBeDeletedFrom`
    * Type: aws:executeAutomation
    * Inputs:
        * `DocumentName`: `Digito-RestoreFromBackup_2020-09-21`
        * `RuntimeParameters`:
            * `AutomationAssumeRole`: {{AutomationAssumeRole}}
            * `SNSTopicARNForManualApproval`: {{SNSTopicARNForManualApproval}}
            * `UserWhoWillApproveCleanRestoreBucket`: {{UserWhoWillApproveCleanRestoreBucket}}
            * `S3BucketToRestoreName`: {{S3BucketWhereObjectsWillBeDeletedFrom}}
            * `S3BackupBucketName` {{S3BucketToRestoreWhereObjectWillBeCopiedTo}}
    * Explanation:
        * Copy all files from the `S3BucketWhereObjectsWillBeDeletedFrom` bucket to the `S3BucketToRestoreWhereObjectWillBeCopiedTo` bucket by shared SSM Document `Digito-RestoreFromBackup_2020-09-21`
1. `CleanS3BucketWhereObjectsWillBeDeletedFrom`
    * Type: aws:executeAutomation
    * Inputs:
        * `DocumentName`: `Digito-CleanS3Bucket_2021-03-03`
        * `RuntimeParameters`:
            * `AutomationAssumeRole`: {{AutomationAssumeRole}}
            * `S3BucketNameToClean`: {{S3BucketWhereObjectsWillBeDeletedFrom}}
    * Explanation:
        * Clean the `S3BucketWhereObjectsWillBeDeletedFrom` bucket by calling shared SSM document  `Digito-CleanS3Bucket_2021-03-03`
    * OnFailure: step: RollbackCurrentExecution
1. `AssertAlarmToBeRed`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `S3UserErrorAlarmName`
    * Outputs: none
    * Explanation:
        * Wait for `S3UserErrorAlarmName` alarm to be `ALARM` 
    * OnFailure: step: RollbackCurrentExecution
1. `RollbackCurrentExecution`
    * Type: aws:executeAutomation
    * Inputs:
        * `DocumentName`: `Digito-RestoreFromBackup_2020-09-21`
        * `RuntimeParameters`:
            * `AutomationAssumeRole`: {{AutomationAssumeRole}}
            * `SNSTopicARNForManualApproval`: {{SNSTopicARNForManualApproval}}
            * `UserWhoWillApproveCleanRestoreBucket`: {{UserWhoWillApproveCleanRestoreBucket}}
            * `S3BucketToRestoreName`: {{S3BucketToRestoreWhereObjectWillBeCopiedTo}}
            * `S3BackupBucketName` {{S3BucketWhereObjectsWillBeDeletedFrom}}
    * Explanation:
        * Copy all files from the `S3BucketToRestoreWhereObjectWillBeCopiedTo` bucket to the `S3BucketWhereObjectsWillBeDeletedFrom` bucket by shared SSM Document `Digito-RestoreFromBackup_2020-09-21`
1. `AssertAlarmToBeGreen`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `S3UserErrorAlarmName`
    * Outputs: none
    * Explanation:
        * Wait for `S3UserErrorAlarmName` alarm to be `OK`
    * isEnd: true

## Outputs
No.