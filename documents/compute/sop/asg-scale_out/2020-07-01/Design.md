# Id
compute:sop:asg-scale_out:2020-07-01

## Intent
Scale out an asg

## Type
Software Outage SOP

## Risk
Small

## Requirements
* Available ASG

## Permission required for AutomationAssumeRole
* autoscaling:UpdateAutoScalingGroup
* autoscaling:DescribeAutoScalingGroups
* autoscaling:DescribeLaunchConfigurations
* autoscaling:CreateLaunchConfiguration
* autoscaling:DeleteLaunchConfiguration
* autoscaling:StartInstanceRefresh
* autoscaling:DescribeInstanceRefreshes
* ec2DescribeLaunchTemplateVersions
* ec2DescribeInstanceTypeOfferings
* ec2CreateLaunchTemplateVersion
* ec2DeleteLaunchTemplateVersions
* ec2RunInstances
* iam:PassRole



## Supports Rollback
Yes.

## Inputs
### AutoScalingGroupName:
* type: String
* description: (Required) The ASG Group Name
### AutomationAssumeRole:
* type: String
* description: 
    (Optional) The ARN of the role that allows Automation to perform
    the actions on your behalf. If no role is specified, Systems Manager Automation
    uses your IAM permissions to run this document.
    default: ''

## Outputs
* `NewDesiredCapacity`: The new desired capacity for the ASG
* `NewMaxSize`: The new max size for the ASG
* `OutputRecoveryTime.RecoveryTime`: recovery time in seconds

## Details of SSM Document steps:
See implementation (implementation already existed when this document was written)