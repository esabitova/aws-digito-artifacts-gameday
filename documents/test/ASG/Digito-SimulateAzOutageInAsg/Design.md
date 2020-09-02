# https://github.com/aws-samples/aws-digito-artifacts-spec/blob/master/components/compute/stateless/compute-stateless-gameday.adoc#test---availability-zone-outage-asg 

# Id
stateless_compute:test:asg-availability_zone_outage:2020/07/23

## Intent
Test that the application can withstand az outage in ASG

## Type
AZ Failure Test

## Risk
Medium

## Requirements
* ASG has more than 1 instance
* There is a synthetic alarm setup for application
* Application should be scaled sufficiently to handle expected traffic with one az loss

## Permission required for AutomationAssumeRole
* autoscaling.describe_auto_scaling_groups
* autoscaling.suspend_processes
* autoscaling.resume_processes
* cloudwatch.describe_alarms
* ec2.terminate_instances

## Supports Rollback
Yes. If executed in rollback mode, any previous asg instance refresh in progress would be cancelled.

## Inputs

### AutoScalingGroupName
  * Description: (Required) Name of AutoScalingGroup
  * Type: String
### AzOutageAlarmName
  * Description: (Required) Alarm for az outage in Asg. This should be red during test and go green after test.
  * Type: String
### SyntheticAlarmName
  * Description: (Required) Name of Synthetic alarm for application. This should be green after the test.
  * Type: String
### TestDurationInMinutes
  * Description: (Required) Test duration in minutes.
  * Type: String
### AutomationAssumeRole:
  * Description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf. See Permissions required above for test.
  * Type: String

## Details
  * Select AZ where majority of instances are in.
  * Prevent new instances in AZ from turning on (use suspendLaunch API)
  * Inject an error to all instances in AZ together (terminate all instances in az)
  * Verify alarms alert in (alarms a)
  * Potentially verify that Synthetic monitor stays green / turns green within x minutes.

## Outputs
The automation execution has no outputs
