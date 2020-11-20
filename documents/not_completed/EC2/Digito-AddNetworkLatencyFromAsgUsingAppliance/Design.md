# Add network latency from instances in autoscaling group to dependency
This document adds network latency from instances in autoscaling group to dependency. You can specify a range of destination ip addresses or a valid aws service from https://docs.aws.amazon.com/general/latest/gr/aws-ip-ranges.html to which latency will be added.

## Requirements
* Public Subnet Id in ASG VPC
* ASG Security group allows access to self for all ip ranges  

## Permission required for AutomationAssumeRole
* autoscaling.describe_auto_scaling_groups
* autoscaling.describe_launch_configurations
* ssm.get_automation_execution
* ec2.authorize_security_group_ingress
* ec2.describe_images
* ec2.describe_route_tables
* ec2.describe_security_groups
* ec2.describe_subnets
* ec2.replace_route 
* ec2.run_instances
* ec2.terminate_instances

## Inputs

### AutoScalingGroupName
  * Autoscaling group for which we need to inject latency
  * Type: String
  * Description: (Required) Name of AutoScalingGroup.
### NetworkLatencyDurationMinutes
  * Duration of test
  * Type: String
  * Description: (Required) Duration of network latency test.
### NetworkLatencyDelayMs:
  * Additional latency to add
  * Type: String
  * Description: (Required) Network delay to be added in ms.
### AutomationAssumeRole:
  * The ARN of the role that allows Automation to perform the actions on your behalf. See Permissions required above for test.
  * Type: String
  * Description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf.
### AwsServiceName:
  * Valid AWS Service from https://docs.aws.amazon.com/general/latest/gr/aws-ip-ranges.html
  * Type: String
  * Description: (Optional) Valid AWS Service from https://docs.aws.amazon.com/general/latest/gr/aws-ip-ranges.html to which latency will be added.
  * Default: ''
### DestinationIpAddressRanges:
  * Additional ip address range to which latency will be added. Specify 0.0.0.0/0 to add latency to all outgoing network traffic.
  * Type: String
  * Description: (Optional) Destination ip address to which latency will be added.
  * Default: ''
### IsRollback:
  * Provide true to rollback effects from previous execution.
  * Type: String
  * Description: (Optional) Provide true to rollback effects from previous execution. 
  * Default: 'false'
### PreviousExecutionId:
  * Previous execution id for which effects will be rolled back 
  * Type: String
  * Description: (Optional) Previous execution id for which effects will be rolled back
  * Default: ''

## Outputs
The automation execution has no outputs
