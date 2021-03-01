# Id

efs:sop:change_provisioned_throughput:2020-10-26

## Intent

Change Provisioned throughput

## Type

Software Outage SOP

## Risk

Medium

## Requirements

* EFS volume with 'provisioned' Throughput Mode.

## Permission required for AutomationAssumeRole

* efs.describe_file_systems ("elasticfilesystem:DescribeFileSystems)
* efs.update_file_system ("elasticfilesystem:UpdateFileSystem")

## Supports Rollback

No.

## Inputs

### FileSystemID

* Description: (Required) The EFS ID.
* Type: String

### ProvisionedThroughput

* Description: (Required) The amount of throughput, in MiB/s, that you want to provision for your file system. Valid
  values are 1-1024.
* Type: Double

### AutomationAssumeRole:

* Description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf.
* Type: String

## Details

1.`ChangeFileSystemProvisionedThroughput`
  * Type: aws:executeAwsApi
  * Inputs:
      * `FileSystemId`: The EFS volume ID (FileSystemID)
      * `ProvisionedThroughputInMibps`: New value for provisioned throughput in Mibps (ProvisionedThroughput)
  * Outputs:
      * `FileSystemId`: Updated EFS volume ID
  * Explanation:
      * Call [UpdateFileSystem](https://docs.aws.amazon.com/efs/latest/ug/API_UpdateFileSystem.html) from `efs`
        service to update provisioned throughput

## Outputs

* `ChangeFileSystemProvisionedThroughput.FileSystemId` The EFS ID
