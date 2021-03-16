# https://us-west-2.console.aws.amazon.com/codesuite/codecommit/repositories/aws-digito-artifacts-spec/browse/refs/heads/master/--/components/compute/stateless/ec2_and_asg/compute-stateless-gameday.adoc?region=us-west-2&lines=185-185
## Id
compute:test:ec2-inject_cpu_load:2020-07-28

## Intent
Test app monitor under load. (see note below)

## Type
HW Instance Failure Test

## Risk
Small

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
* cloudwatch:GetMetricStatistics
* iam:PassRole

## Supports Rollback
Yes. If executed in rollback mode, any previous EC2 instance CPU injection will be terminated.

## Inputs
### CpuUtilizationAlarmName:
   * type: String
   * description: (Required) EC2 CPUUtilization alarm which should be triggerred
### InstanceId:
   * type: String
   * description: (Required) EC2 instance id (no need in case of rollback)
### Duration:
   * type: String
   * description: (Optional) The duration of the attack in seconds (default/recommended 300)
   * default: '300'
### NumCpuCores:
   * type: String
   * description: (Optional) Number of CPU cores to be impacted (default 0 - all)
   * default: '0'
### CpuLoadPercentage:
   * type: String
   * description: (Optional) The ASG EC2 instance CPU load percentage (default 1%)
   * default: '1'
### IsRollback:
   * type: String
   * description: (Optional) Provide true to terminate stress testing
   * default: 'false'
### PreviousExecutionId:
   * type: String
   * description: (Optional) Previous execution id for which resources stress testing should be terminated (need in case of rollback)
   * default: ''

## Details
  * Start a CPU hog on instance for X minutes
  * Verify alarm (a) is triggered

    Note: this may or may not be a relevant use-case for customers. 
    high CPU load may be expected on some systems and may not be an issue on other EC2 instances.. depends on the type of work they are running.

    If it is expected, the customer either has a custom way to deal with it, or needs to be alerted to it. Either way he needs a low level monitor and to test this monitor.


## Outputs
The automation execution has no outputs