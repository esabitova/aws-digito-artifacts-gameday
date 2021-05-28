# Id
ebs:sop:restore_from_backup:2020-05-26

## Intent
Restore EBS volume from backup

## Type
Software

## Risk
Small

## Requirements
* An EBS Volume Snapshot with status "completed"

## Permission required for AutomationAssumeRole
* ec2:CreateVolume
* ec2.DescribeVolumes
* ec2.DescribeVolumeStatus

## Supports Rollback
No.

## Inputs
### EBSSnapshotIdentifier:
* type: String
* description: (Required) The identifier of the snapshot to restore
### TargetAvailabilityZone
* Description: (Required) Availability Zone in which to create the volume. 
* Type: String
### VolumeType:
* type: String
* description: (Optional) The Volume Type. (If omitted the default would be gp2) 
### VolumeIOPS:
* type: String
* description: (Optional) The number of I/O operations per second (IOPS).
### AutomationAssumeRole:
* type: String
* description: 
    (Optional) The ARN of the role that allows Automation to perform
    the actions on your behalf. If no role is specified, Systems Manager Automation
    uses your IAM permissions to run this document.
    default: ''

## Outputs
* `EBSVolumeIdentifier`: The EBS Volume identifier for the restored volume
* `OutputRecoveryTime.RecoveryTime`: recovery time in seconds
* `Snapshot.StartTime`: The timestamp when the snapshot was taken (backup point)

## Details of SSM Document steps:
1. `RecordStartTime`
    * Type: aws:executeScript
    * Outputs:
        * `StartTime`
    * Explanation:
        * Start the timer when SOP starts
2. `DescribeSnapshot`
   * Type: aws:executeAwsApi
   * Inputs:
       * `EBSSnapshotIdentifier`: EBS Snapshot to restore
   * Outputs:
       * `VolumeId`: Original volume
       * `State`: snapshot state
       * `StartTime`: The timestamp when the snapshot was taken (backup point)
   * Explanation:
       * Get current snapshot information, validate that the state is "completed"
         calling [DescribeSnapshot](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeSnapshots.html)
3. `Check`
    * Type: aws:branch
    * Inputs:
        * `VolumeType`
        * `VolumeIOPS`
    * Outputs: none
    * Explanation:
        * If `VolumeId` != `vol-ffffffff` and (
            `VolumeType` is undefined or 
            (`VolumeIOPS` is undefined and `VolumeType` != `gp2`))
            go to the step `DescribeVolume`. 
        * else, proceed to the step `CalculateAZAndVolumeType`         
4. `DescribeVolume`
   * Type: aws:executeAwsApi
   * Inputs:
       * `VolumeId`: The EBS Volume that created the snapshot
   * Outputs:
       * `OriginalVolumeType`: The original volume type
       * `OriginalVolumeIOPS`: The original volume iops
   * Explanation:
       * Get volume information
         calling [DescribeVolumes](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeVolumes.html)         
5. `CalculateAZAndVolumeType`
    * Type: aws:executeScript
    * Inputs:
       * `OriginalVolumeType`: The original volume type
       * `OriginalVolumeIOPS`: The original volume iops
       * `VolumeType`: The requested volumeType (optional)
       * `VolumeIOPS`: The requested IOPS (optional)
    * Outputs:
        * `TargetVolumeType`: The target volume type
        * `TargetVolumeIOPS`: The target volume iops
    * Explanation:
        * Calculate the target AZ/VolumeType/IOPS
        * Requested Params override Original params, use defaults if neither exists:
            * `TargetVolumeType` = `VolumeType` or `OriginalVolumeType`
            * `TargetVolumeIOPS` = `VolumeIOPS` or `OriginalVolumeIOPS`  
5. `CreateVolume`
   * Type: aws:executeAwsApi
   * Inputs:
        * `EBSSnapshotIdentifier`: The Snapshot id from which to create the volume 
        * `AvailabiltyZone`: The volume AZ
        * `TargetVolumeType`: The target volume type
        * `TargetVolumeIOPS`: The target volume iops
    * Outputs:
        * `CreatedVolumeId`: The id of the created volume
   * Explanation:
       * Create the new volume
         calling [CreateVolume](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_CreateVolume.html)
6. `WaitUntilVolumeAvailable`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `CreatedVolumeId`
    * PropertySelector: `$.VolumeStatuses..VolumeStatus.Status`
    * DesiredValues: `ok`
    * Explanation:
        * Wait until EBS volume status is running        
7. `OutputRecoveryTime`
    * Type: aws:executeScript
    * Inputs:
        * `RecordStartTime.StartTime`
    * Outputs:
        * `RecoveryTime`
    * Explanation:
        * Measures recovery time
