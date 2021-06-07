# https://us-west-2.console.aws.amazon.com/codesuite/codecommit/repositories/aws-digito-artifacts-spec/browse/refs/heads/master/--/components/compute/stateless/ec2_and_asg/compute-stateless-gameday.adoc?region=us-west-2&lines=185-185
## Id
compute:test:asg-kill_process:2020-07-28

## Intent
Test app if process suddenly dies.

## Type
HW Instance Failure Test

## Risk
Small

## Requirements
* EC2 instance with Linux OS 
* There is a synthetic alarm setup for application

## Permission required for AutomationAssumeRole
* ssm:GetParameters
* ssm:SendCommand
* ssm:ListCommands
* ssm:ListCommandInvocations
* ssm:DescribeInstanceInformation
* cloudwatch:DescribeAlarms
* cloudwatch:DescribeAlarmHistory

## Supports Rollback
No

## Inputs
### AutomationAssumeRole:
   * type: String
   * description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf
### AutoScalingGroupName:
   * type: String
   * description: (Required) AutoScalingGroup name.
### PercentageOfInstances
   * type: Integer
   * description: (Optional) Percentage of ASG EC2 instances to be impacted
   * default: 1
### MultipleUnhealthyHostsAlarmName:
   * type: String
   * description: (Required) MultipleUnhealthyHostsAlarmName which should be triggerred.
### ProcessName:
   * type: String
   * description: (Optional) Process name to be killed
### ExpectedRecoveryTimeInMinutes:
   * type: String
   * description: (Optional) The expected recovery time after process dies (default 5)
   * default: '5'

## Details
  * Figure out the instances to run on (round up)
  * For each instance, Figure out the process id to kill
  * For each instance, Send the signal to the processes
  * Either verify app recovered (after Y time alarm is green) or verify that alarm triggered.

## Outputs
The automation execution has no outputs