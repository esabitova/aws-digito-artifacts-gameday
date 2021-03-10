# https://code.amazon.com/packages/AwsDigitoAssessmentRules/blobs/e0c9fb58c0f340b95b5a8f818c33cf6f0aa02f11/--/components/compute/stateless/ec2_and_asg/compute-stateless-gameday.adoc#L213
## Id
compute:test:ec2-inject_memory_load:2020-07-28

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
Yes. If executed in rollback mode, any previous EC2 instance memory injection will be terminated.

## Inputs
### AutomationAssumeRole:
   * type: String
   * description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf
### InstanceId:
   * type: String
   * description: (Required) EC2 instance id
### MemoryUtilizationAlarmName:
   * type: String
   * description: (Required) EC2 Memory Utilization alarm which should be triggerred
### Duration:
   * type: String
   * description: (Optional) The duration of the attack in seconds (default/recommended 120)
   * default: '120'
### Vm:
   * type: String
   * description: (Optional) Number of VM memory stressors
   * default: '1'
### MemoryLoadPercentage:
   * type: String
   * description: (Optional) The EC2 instance memory load percentage (default 1%)
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
  * Figure out the amount of memory to grab from available free memory
  * Start a memory load for the amount of memory in bytes on instance for X minutes
  * Verify alarm (a) is triggered

  Note: this may or may not be a relevant use-case for customers. 
  Some workloads have variable memory needs and may fail if memory becomes unavailable.

  If it is expected, the customer either has a custom way to deal with it, or needs to be alerted to it.
  Either way he needs a low level monitor and to test this monitor.

 * Customer may tweak to verify his recovery process did run. 
 * Customer may tweak to add calls to his app to make sure the app is accepting inputs that will need memory (we can’t assume this is running on production)

## Outputs
The automation execution has no outputs