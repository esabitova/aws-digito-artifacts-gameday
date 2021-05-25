# Id
compute:sop:ec2_reboot:2020-05-20

## Intent
Reboot the ec2 instance

## Type
HW Instance Failure Test

## Risk
Small

## Requirements
* EC2 Instance

## Permission required for AutomationAssumeRole
* ec2.RebootInstances
* ec2.DescribeInstanceStatus

## Supports Rollback
No.

## Inputs

### EC2InstanceIdentifier
  * Description: (Required) EC2 Instance Identifier
  * Type: String
### AutomationAssumeRole:
  * Description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf.
  * Type: String
  
## Outputs
  * `OutputRecoveryTime.RecoveryTime`: recovery time in seconds

## Details of SSM Document steps:
1. `RecordStartTime`
    * Type: aws:executeScript
    * Outputs:
        * `StartTime`
    * Explanation:
        * Start the timer when SOP starts
2. `RebootEC2Instance`
   * Type: aws:executeAwsApi
   * Inputs:
      * `EC2InstanceIdentifier`
   * Explanation:
       * Reboot DB instance by calling [RebootInstances](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_RebootInstances.html)
3. `WaitUntilInstancesAvailable`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `EC2InstanceIdentifier`
    * PropertySelector: `$.InstanceStatuses..InstanceState`
    * DesiredValues: `running`
    * Explanation:
        * Wait until ec2 instance become available
4. `OutputRecoveryTime`
    * Type: aws:executeScript
    * Inputs:
        * `RecordStartTime.StartTime`
    * Outputs:
        * `RecoveryTime`
    * Explanation:
        * Measures recovery time
