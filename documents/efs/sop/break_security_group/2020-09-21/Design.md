# Id

efs:test:break_security_group:2020-09-21

## Intent

Test EFS behavior after breaking security group id

## Type

AZ Outage Test

## Risk

High

## Requirements

* EFS volume
* A EC2 instance with a EFS volume mounted  
* The security groups associated with EFS must allow inbound access for the TCP protocol on the NFS (port 2049) port from other AWS service on which you want to mount the file system.

## Permission required for AutomationAssumeRole

* elasticfilesystem:DescribeMountTargets
* elasticfilesystem:DescribeMountTargetSecurityGroups
* elasticfilesystem:ModifyMountTargetSecurityGroups
* cloudwatch:DescribeAlarms
* ssm:GetAutomationExecution
* ssm:GetParameters

## Supports Rollback

Yes. The script backups existing Security Groups assigned and restores it when the specified alarms fires. Users can run the script with `IsRollback` and `PreviousExecutionId` to rollback changes from the previous run.

## Inputs

### `FileSystemId`

* Description: (Required) The EFS file system ID.
* Type: String

### `ClientConnectionsAlarmName`:

* type: String
* description: (Required) Alarm which should be green before and after test, red after the injection of the failure. Recommended alarm is based on the ClientConnections metric.

### `AutomationAssumeRole`:

* Description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf. See Permissions required above for test.
* Type: String

### `MountTargetIds`:

* type: StringList
* description: (Optional) The list of identifiers of the mount targets. The script disassociates security group(-s) from mount target(-s). Empty list means *ALL* targets in randomly selected AZ of the current Region. Provided as a YAML list

### `IsRollback`:

* type: Boolean
* description: (Optional) Run rollback step of the given previous execution (parameter `PreviousExecutionId`)
* default: False

### `PreviousExecutionId`:

* type: Integer
* description: (Optional) The id of previous execution of the current script
* default: 0

## Details

1. `CheckIsRollback`
    * Type: aws:branch
    * Inputs:
        * `IsRollback`
    * Outputs: none
    * Explanation:
        * `IsRollback` it true, continue with `PrepareFileSystemId` step
        * `IsRollback` it false, continue with `AssertAlarmToBeGreenBeforeTest` step
1. `PrepareFileSystemId`
    * Type: aws:executeScript
    * Inputs:
        * `PreviousExecutionId`
    * Outputs:
        * `FileSystemId`: The FileSystemId from the previous execution
    * Explanation:
        * Get value of SSM Document output from the previous execution using `PreviousExecutionId`:
            * `FileSystemId`
1. `CheckInputParameters`
    * Type: aws:branch
    * Inputs:
        * `PrepareFileSystemId.FileSystemId`
        * `FileSystemId`
    * Outputs: none
    * Explanation:
        * Fail if input parameters are not equal. Otherwise, move to the next step.
1. `PrepareMountTargetIds`
    * Type: aws:executeScript
    * Inputs:
        * `PreviousExecutionId`
        * `StepName`: `SearchForMountTargetIds`
    * Outputs:
        * `MountTargetIds`
    * Explanation:
        * Get value of SSM Document output from the previous execution's step using `PreviousExecutionId`
1. `PrepareSecurityGroups`
    * Type: aws:executeScript
    * Inputs:
        * `PreviousExecutionId`
        * `StepName`: `BackupEfsSecurityGroups`
    * Outputs:
        * `MountTargetIdToSecurityGroupsMap`
    * Explanation:
        * Get value of SSM Document output from the previous execution's step using `PreviousExecutionId`
1. `RollbackPreviousExecution`
    * Type: aws:executeAwsApi
    * Inputs:
        * `PrepareMountTargetIds.MountTargetId`
        * `PrepareSecurityGroups.MountTargetIdToSecurityGroupsMap`
    * Explanation:
        * Call https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/efs.html#EFS.Client.modify_mount_target_security_groups
1. `AssertAlarmToBeGreenBeforeTest`
    * Type: aws:assertAwsResourceProperty
1. `SearchForMountTargetIds`
    * Type: aws:executeScript
    * Inputs:
        * `FileSystemId`
        * `MountTargetIds`
    * Outputs:
        * `MountTargetIds`
    * Explanation:
        * If `MountTargetIds` is empty, get the list of mount targets by `FileSystemId` and leave only those `MountTargetIds` which are related to the randomly selected AZ from the list of all existing AZs occurred in all found mount targets. Use the apis: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/efs.html#EFS.Client.describe_file_systems to get all MountTargetIds and https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/efs.html#EFS.Client.describe_mount_targets to get their AZs 
        * If `MountTargetIds` is not empty, find all its members in the list of mount targets by `FileSystemId`. If some members from input parameter doesn't appear in the list of mount targets, return exception.
1. `BackupEfsSecurityGroups`
    * Type: aws:executeScript
    * Inputs:
        * `MountTargetIds`
    * Outputs:
        * `MountTargetIdToSecurityGroupsMap`
    * Explanation:
        * Call https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/efs.html#EFS.Client.describe_mount_target_security_groups
        * Outputs MapList `MountTargetIdToSecurityGroupsMap` with a map of mount targets and their security groups
1. `ModifyMountTargetSecurityGroups`
    * Type: aws:executeAwsApi
    * Inputs:
        * `MountTargetIds`
    * Explanation:
        * Call https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/efs.html#EFS.Client.modify_mount_target_security_groups with an empty list as a `SecurityGroups` argument
    * OnFailure: step: `RollbackChanges`
1. `AssertAlarmToBeRed`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `ClientConnectionsAlarmName`
    * Outputs: none
    * Explanation:
        * Wait for `ClientConnectionsAlarmName` alarm to be `ALARM` for 600 seconds
    * OnFailure: step: `RollbackChanges`
1. `RollbackCurrentChanges`
    * Type: aws:executeScript
    * Inputs:
        * `MountTargetIds`
        * `BackupEfsSecurityGroups.MountTargetIdToSecurityGroupsMap`
    * Explanation:
        * Call https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/efs.html#EFS.Client.modify_mount_target_security_groups
1. `AssertAlarmToBeGreen`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `ClientConnectionsAlarmName`
    * Outputs: none
    * Explanation:
        * Wait for `ClientConnectionsAlarmName` alarm to be `OK` for 600 seconds
    * isEnd: true

## Outputs

No