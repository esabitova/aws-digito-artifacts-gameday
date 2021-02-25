## Id
compute:test:ec2-network_unavailable:2020-07-23

## Intent
Test that the application correctly alerts if EC2 network is unavailable.

## Type
HW Instance Failure Test

## Risk
High

## Requirements
* EC2 instance with Linux OS 
* There is a synthetic alarm setup for application

## Permission required for AutomationAssumeRole
* ssm:SendCommand
* ssm:ListCommands
* ssm:ListCommandInvocations
* ssm:DescribeInstanceInformation
* ssm:GetAutomationExecution
* ssm:CancelCommand
* cloudwatch:DescribeAlarms
* ec2:RebootInstances

## Supports Rollback
Yes. Reboots instance to cancel impact

## Inputs
### InstanceId:
   * type: String
   * description: (Required) EC2 instance id
### SyntheticAlarmName:
   * type: String
   * description: (Required) Application synthetic alarm which should be trigerred
### Duration:
   * type: String
   * description: (Optional) The duration of the attack in seconds (default/recommended 300)
   * default: '300'
### IsRollback:
   * type: String
   * description: (Optional) Provide true to rollback previous execution
   * default: 'false'
### PreviousExecutionId:
   * type: String
   * description: (Optional) Previous execution id for which test should be rolled back (need in case of rollback)
   * default: ''


## Details
  * Drop all outgoing/incoming network traffic on instance for X minutes
  * Verify alarm is triggered
  * After test duration, alarm should go back to green

## Outputs
The automation execution has no outputs