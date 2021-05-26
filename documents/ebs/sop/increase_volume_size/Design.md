# Id
ebs:sop:increase_volume_size:2020-05-26

## Intent
Increase EBS volume size

## Type
Software

## Risk
Small

## Requirements
* An EBS Volume attached to a running EC2 instance (linux)
* EBS must have a single partition, the first partition size will increase

## Permission required for AutomationAssumeRole
* ec2:ModifyVolume
* ssm:SendCommand

## Supports Rollback
No.

## Inputs
### EBSVolumeIdentifier:
* type: String
* description: (Required) The identifier of the volume requiring increase of size
### SizeGiB
* Description: (Required) The target size to increase the volume to (in GiB) 
* Type: String
### AutomationAssumeRole:
* type: String
* description: 
    (Optional) The ARN of the role that allows Automation to perform
    the actions on your behalf. If no role is specified, Systems Manager Automation
    uses your IAM permissions to run this document.
    default: ''

## Outputs
* `OutputRecoveryTime.RecoveryTime`: recovery time in seconds

## Details of SSM Document steps:
1. `RecordStartTime`
    * Type: aws:executeScript
    * Outputs:
        * `StartTime`
    * Explanation:
        * Start the timer when SOP starts
2. `FindDeviceAndCurrentSize`
   * Type: aws:executeAwsApi
   * Inputs:
       * `EBSVolumeIdentifier`: EBS Volume to modify size
   * Outputs:
       * `Device`: The attached device (/dev/xvda)
       * `CurrentSizeGiB`: The current size of the volume 
       * `EC2InstanceIdentifier`: The current attached instance 
   * Explanation:
       * DescribeVolume to get current attached device and size,
         calling [DescribeVolume](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeVolume.html)
3. `ValidateSize`         
    * Type: aws:branch
    * Inputs:
        * `SizeGib`
        * `CurrentSizeGiB`
    * Outputs: none
    * Explanation:
        * `SizeGib` <= `CurrentSizeGiB` it true, continue with `End` step
        * else continue with `ModifyVolume`
4. `ModifyVolume`
   * Type: aws:executeAwsApi
   * Inputs:
       * `EBSVolumeIdentifier`: EBS Volume to modify size
       * `SizeGiB`: The required new size
   * Explanation:
       * Modify Volume size,
         calling [ModifyVolume](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_ModifyVolume.html)
5. `ChangeVolumeSize`
   * Type: aws:sendCommand
   * Inputs:
       * `EBSVolumeIdentifier`: EBS Volume to modify size
       * `EC2InstanceIdentifier`: The Ec2 instance to which the volume is connected.
       * `Device`: The device the volume is mounted on (Required to increase the size)
       * `SizeGiB`: The required new size
   * Explanation:
       * Send the command to the Ec2
       * `sudo growpart ${Device} 1`
       * for EBS use `sudo resize2fs ${Device}1`
       * for XFS use `sudo xfs_growfs -d ${volume mount point}` 
       refer to [ModifyOSSize](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/recognize-expanded-volume-linux.html)
       or [EBSVolumeSizeAutomation](https://aws.amazon.com/blogs/storage/automating-amazon-ebs-volume-resizing-with-aws-step-functions-and-aws-systems-manager/)
6. `OutputRecoveryTime`
    * Type: aws:executeScript
    * Inputs:
        * `RecordStartTime.StartTime`
    * Outputs:
        * `RecoveryTime`
    * Explanation:
        * Measures recovery time
