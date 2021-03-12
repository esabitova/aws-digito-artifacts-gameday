## Id
compute:test:asg-network_unavailable:2020-07-23

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
* ssm:GetParameters
* ssm:SendCommand
* ssm:ListCommands
* ssm:ListCommandInvocations
* ssm:DescribeInstanceInformation
* ssm:GetAutomationExecution
* ssm:CancelCommand
* cloudwatch:DescribeAlarms
* autoscaling:DescribeAutoScalingGroups

## Supports Rollback
No. ASG should replace unhealthy instances.

## Inputs
### AutoScalingGroupName:
   * type: String
   * description: (Required) AutoScalingGroup name
### MultipleUnhealthyHostsAlarmName:
   * type: String
   * description: (Required) Multiple Unhealthy Hosts alarm should be trigerred
### PercentageOfInstances
   * type: Integer
   * description: (Optional) Percentage of ASG EC2 instances to be impacted
   * default: 1
### DurationInMinutes:
   * type: String
   * description: (Optional) The duration of the attack in minutes (default/recommended 5)
   * default: '5'

## Details
  * Drop all outgoing/incoming network traffic on instance for X minutes
  * Verify multiple unhealthy hosts alarm alarm is triggered
  * After test duration, multiple unhealthy hosts alarm should go back to green

## Outputs
The automation execution has no outputs
