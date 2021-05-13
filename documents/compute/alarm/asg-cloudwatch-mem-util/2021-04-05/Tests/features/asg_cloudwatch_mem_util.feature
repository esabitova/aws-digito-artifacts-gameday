@asg @integration @alarm @memory
Feature: Alarm Setup - ASG Memory Utilization (via CloudWatch Agent)
  Scenario: Lease ASG from resource manager and test attach an alarm from Document
    Given the cloud formation templates as integration test resources
      |CfnTemplatePath                                                       |ResourceType|InstanceType |
      |resource_manager/cloud_formation_templates/AsgCfnTemplate.yml         |ON_DEMAND   |t2.small     |
      |resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml    |SHARED      |             |
    When alarm "compute:alarm:asg-cloudwatch-mem-util:2021-04-05" is installed
      |AutoScalingGroupName                               | Threshold | SNSTopicARN                       |
      |{{cfn-output:AsgCfnTemplate>AutoScalingGroupName}} | 1         | {{cfn-output:SnsForAlarms>Topic}} |
    Then assert metrics for all alarms are populated

