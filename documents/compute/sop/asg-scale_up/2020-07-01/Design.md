# Id
compute:sop:asg-scale_up:2020-07-01

## Intent
Scale up ASG instances to the next instance type

## Type
Software Outage SOP

## Risk
Small

## Requirements
* Available ASG

## Permission required for AutomationAssumeRole
* autoscaling:UpdateAutoScalingGroup
* autoscaling:DescribeAutoScalingGroups



## Supports Rollback
Yes.

## Inputs
### AutoScalingGroupName:
* type: String
* description: (Required) The Name of the ASG to scale-up
### AutomationAssumeRole:
* type: String
* description: 
    (Optional) The ARN of the role that allows Automation to perform
    the actions on your behalf. If no role is specified, Systems Manager Automation
    uses your IAM permissions to run this document.
    default: ''

## Outputs
* `OutputRecoveryTime.RecoveryTime`: recovery time in seconds

## Details of SSM Document steps:
See implementation (implementation already existed when this document was written)