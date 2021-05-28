# Id
compute:sop:ec2_scale_up:2020-05-20

## Intent
Scale up an ec2 to the successor instance type

## Type
Software Outage SOP

## Risk
Small

## Requirements
* Available EC2 Instance

## Permission required for AutomationAssumeRole
* ec2:StopInstances
* ec2.StartInstances
* ec2.DescribeInstances
* ec2.ModifyInstanceAttribute



## Supports Rollback
Yes.

## Inputs
### EC2InstanceIdentifier:
* type: String
* description: (Required) EC2 Instance Identifier
### EC2InstanceTargetInstanceType:
* type: String
* description: (Optional) Override target InstanceType for scale-up (default is to calculate the next instance type)
### AutomationAssumeRole:
* type: String
* description: 
    (Optional) The ARN of the role that allows Automation to perform
    the actions on your behalf. If no role is specified, Systems Manager Automation
    uses your IAM permissions to run this document.
    default: ''

## Outputs
* `TargetInstanceType`: The instance type after the scale-up
* `OutputRecoveryTime.RecoveryTime`: recovery time in seconds

## Details of SSM Document steps:
1. `RecordStartTime`
    * Type: aws:executeScript
    * Outputs:
        * `StartTime`
    * Explanation:
        * Start the timer when SOP starts
2. `DescribeEC2Instance`
   * Type: aws:executeAwsApi
   * Inputs:
       * `EC2InstanceId`: ec2 instance we want to scale-up
   * Outputs:
       * `InstanceType`: information about instance type
   * Explanation:
       * Get current instance type
         calling [DescribeInstances](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeInstances.html)
3. `CalculateTargetType`
    * Type: aws:executeScript
    * Inputs:
        * `InstanceType`: the current instanceType
        * `EC2InstanceTargetInstanceType`: An override for the instance type 
    * Outputs:
        * `TargetInstanceType`: use EC2InstanceTargetInstanceType if not null, or calculate the successor of instance type
    * Explanation:
        * Calculate the successor of instance type (for example t2.small -> t2.medium)
4. `StopEC2Instance`
   * Type: aws:executeAwsApi
   * Inputs:
       * `EC2InstanceId`
   * Explanation:
       * Stops the EC2 Instance
         calling [StopInstances](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_StopInstances.html)
5. `ModifyInstanceAttributes`
    * Type: aws:executeAwsApi
    * Inputs:
        * `EC2InstanceId`: ec2 instance we want to scale-up
    * Explanation:
        * Modify instance type by calling AWS API action: [ModifyInstanceAttributes](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_ModifyInstanceAttribute.html)
6. `ValidateInstanceTypeChanged`
   * Type: aws:executeAwsApi
   * Inputs:
       * `EC2InstanceId`: ec2 instance we want to scale-up
       * `TargetInstanceType`: target instance type
   * Outputs:
       * `InstanceType`: information about instance type
   * Explanation:
       * Get current instance type and compare it with TargetInstanceType
         calling [DescribeInstances](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeInstances.html)
7. `StartInstance`
   * Type: aws:executeAwsApi
   * Inputs:
       * `EC2InstanceId`: ec2 instance we want to scale-up
   * Explanation:
       * Starts the modified instance
         calling [StartInstances](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_StartInstances.html)
8. `WaitUntilInstancesAvailable`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `EC2InstanceIdentifier`
    * PropertySelector: `$.InstanceStatuses..InstanceState`
    * DesiredValues: `running`
    * Explanation:
        * Wait until ec2 instance become available        
9. `OutputRecoveryTime`
    * Type: aws:executeScript
    * Inputs:
        * `RecordStartTime.StartTime`
    * Outputs:
        * `RecoveryTime`
    * Explanation:
        * Measures recovery time
