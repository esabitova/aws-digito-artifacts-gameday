# Id

s3:sop:restore_to_previous_version:2020-09-21

## Intent

Used to restore an S3 object into previous version

## Type

Software Outage SOP

## Risk

Small

## Requirements

* S3 bucket with versioning enabled

## Permission required for AutomationAssumeRole

* s3:ListObjectVersions
* s3:CopyObject

## Supports Rollback

No.

## Inputs

### `S3BucketName`

* Description: (Required) The S3 Bucket Name.
* Type: String

### `S3BucketObjectKey`

* Description: (Required) The S3 Bucket Object Key.
* Type: String

### `AutomationAssumeRole`:

* Description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf. See Permissions required above for test.
* Type: String

## Details

1. `RestoreToThePreviousVersion`
    * Type: aws:executeScript
    * Inputs:
        * `S3BucketName`
        * `S3BucketObjectKey`
    * Outputs:
        * `RestoreTimeSeconds`: The duration of restore to the previous version
        * `OldVersion`: The old version which was before the restore process
        * `ActualVersion`: The new version which became the latest after the restore process
    * Explanation:
        * Call [list_object_versions](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.list_object_versions) to get all versions of the `S3BucketObjectKey`
          object in the `S3BucketName` bucket
        * Choose the previous version from the response above if it exists. Otherwise, log the error and quit
        * Copy selected version to the same bucket by using multipart upload in the [copy](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.copy) method and passing configured [boto3.s3.transfer.TransferConfig](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/customizations/s3.html#boto3.s3.transfer.TransferConfig) and specifying the
          `VersionId` argument as the selected previous version
        * Output the restore time, old version and actual version 

## Outputs

* `RestoreToThePreviousVersion.RestoreTimeSeconds` : The duration of restore to the previous version
* `RestoreToThePreviousVersion.OldVersion` : The old version which was before the restore process
* `RestoreToThePreviousVersion.ActualVersion` : The new version which became the latest after the restore process
