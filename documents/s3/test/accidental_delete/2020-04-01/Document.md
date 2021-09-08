# Id
s3:test:accidental_delete:2020-04-01

## Document Type
Automation

## Description
Accidental delete is testing the case where all versions of files in the bucket were deleted, and we are restoring from the backup bucket

## Disruption Type
SOFTWARE

## Risk
SMALL

## Permissions required
    * s3:DeleteObject
    * s3:GetObject
    * s3:GetObject*
    * s3:DeleteObjectVersion
    * s3:ListBucket
    * s3:ListBucketVersions
    * s3:ListObjectsV2
    * s3:ListObjectVersions
    * s3:PutObject
    * ssm:StartAutomationExecution
    * iam:PassRole
    * ssm:GetAutomationExecution
    * sns:Publish
    * ssm:GetParameters
    * cloudwatch:DescribeAlarms

## Depends On
    * Digito-RestoreFromBackup_2020-09-21
    * Digito-CleanS3BucketUtil_2021-03-03

## Supports Rollback
Yes

## Recommended Alarms
    * S3UserErrorAlarmName : s3:alarm:health-4xxErrors_count:2020-04-01

## Inputs
### `S3BucketWhereObjectsWillBeDeletedFrom`
    * type: String
    * description: (Required) The S3 Bucket Name where objects will be deleted.
### `S3BucketToRestoreWhereObjectWillBeCopiedTo`
    * type: String
    * description: (Required) The S3 Bucket Name where objects will be copied.
### `AutomationAssumeRole`
    * type: String
    * description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf.
### `S3UserErrorAlarmName`
    * type: String
    * description: (Required) ARN of the role that allows Automation to perform the actions on your behalf.
### `SNSTopicARNForManualApproval`
    * type: String
    * description: (Required) The ARN of the SNS Topic where a user will receive the notification about the manual approval of bucket clean-up if some files exist there.
### `IAMPrincipalForManualApproval`
    * type: String
    * description: (Required) ARN of AWS authenticated principal who are able to either approve or reject the clean-up of bucket if there are some files. Can be either an AWS Identity and Access Management (IAM) user name or IAM user ARN or IAM role ARN or IAM assume role user ARN
### `IsRollback`
    * type: String
    * description: (Optional) Provide true to cleanup appliance created in previous execution. Can be true or false
### `PreviousExecutionId`
    * type: String
    * description: (Optional) Previous execution id for which resources need to be cleaned up.
### `ForceCleanBucketToRestoreWhereObjectWillBeCopiedTo`
    * type: Boolean
    * description: (Optional) If it is true, approve cleaning of the bucket automatically where objects will be copied to if they exist there.
Otherwise, give a user a chance to decide. It is false by default.

## Outputs
None
