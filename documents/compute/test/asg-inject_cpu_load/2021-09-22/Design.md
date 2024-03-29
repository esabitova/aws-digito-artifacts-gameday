# https://github.com/aws-samples/aws-digito-artifacts-spec/blob/master/components/compute/stateless/compute-stateless-gameday.adoc#test---inject-cpu-load-to-asg
# Id
compute:test:asg-inject_cpu_load:2020/07/28

## Intent
Test app performance under high CPU load. 

## Type
HW Instance Failure Test

## Risk
High

## Requirements
* ASG has more than 1 instance
* There is a synthetic alarm setup for application
* Only AmazonLinux instances are supported 

## Permission required for AutomationAssumeRole
* autoscaling.describe_auto_scaling_groups
* ec2.describe_instance_status
* cloudwatch:describe_alarms
* cloudwatch:get_metric_statistics
* iam:pass_role

## Supports Rollback
Rollback is supported to terminate stress testing in case if critical application alarm (SyntheticAlarm) is triggered.

## Inputs

### AutomationAssumeRole
  * type: String
  * description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf
### AutoScalingGroupName
  * type: String
  * description: (Required) Name of auto scaling group
### CpuUtilizationAlarmName:
  * type: String
  * description: (Required) ASG CPUUtilization alarm which should be green after test
### DurationSeconds
  * type: String
  * description: (Optional) The duration of the attack in seconds (default/recommended 300)
  * default: '300'
### Cpu
  * type: String
  * description: (Optional) Number of CPU cores to be impacted (default 0 - all)
  * default: '0'
### LoadPercent
  * type: String
  * description: (Optional) The ASG EC2 instance CPU load percentage (default 1%)
  * default: '1'
### PercentageOfInstances
  * type: Integer
  * description: (Optional) Percentage of ASG EC2 instances to be impacted
  * default: 1
### ExpectedRecoveryTime
  * type: String
  * description: (Optional) Expected ASG EC2 instances recovery time in seconds
  * default: '1'
### IsRollback
  * type: String
  * description: (Optional) Provide true to terminate stress testing
  * default: 'false'
### PreviousExecutionId
  * type: String
  * description: (Optional) Previous execution id for which resources stress testing should be terminated
  * default: ''
  
## Details
  * Get healthy ASG EC2 instance ids.  
  * Get list of ASG EC2 instance ids which size is based on given percentage of instances should be stressed.
  * Run CPU stress on chosen instances based on previous step for given time duration.
  * Wait for given expected recovery time duration.
  * Verify critical application alarm is in state 'OK' after recovery.
  * Verify stress testing actually happened, by checking EC2 corresponding metric data points.
  * In case of rollback stress testing will be terminated on EC2 machines.
 
## Outputs
The automation execution has no outputs
