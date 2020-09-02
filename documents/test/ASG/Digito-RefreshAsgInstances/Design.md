# https://github.com/aws-samples/aws-digito-artifacts-spec/blob/master/components/compute/stateless/compute-stateless-gameday.adoc#test---recover-after-all-nodes-replaced
# Id
stateless_compute:test:asg-node_replace:2020/07/23

## Intent
Test that the application stays up even if all instances are replaced. This proves that the app will work even with fresh installs.

## Type
HW Instance Failure Test

## Risk
Small

## Requirements
* ASG has more than 1 instance
* There is a synthetic alarm setup for application

## Permission required for AutomationAssumeRole
* autoscaling.describe_auto_scaling_groups
* ec2.terminate_instances

## Supports Rollback
Yes. If executed in rollback mode, any previous asg instance refresh in progress would be cancelled.

## Inputs

### AutoScalingGroupName
  * Description: (Required) Name of AutoScalingGroup
  * Type: String
### SyntheticAlarmName
  * Description: (Required) Name of Synthetic alarm for application. This should be green after the test.
  * Type: String
### AutomationAssumeRole:
  * Description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf. See Permissions required above for test.
  * Type: String

## Details
  * Stop/Terminate each instance in the ASG (not all at once. use percent of instances )
  * Wait for instances to be replaced
  * Verify monitor stays green

## Outputs
The automation execution has no outputs
