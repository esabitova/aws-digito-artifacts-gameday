@asg @integration @alarm @memory
Feature: Alarm Setup - ASG Memory Utilization (via CloudWatch Agent)
  Scenario: Lease ASG from resource manager and test attach an alarm from Document
    Given the cached input parameters
      |AlarmName               |
      |  ASGMemoryUtilization  |
    And the cloud formation templates as integration test resources
      |CfnTemplatePath                                                       |ResourceType|InstanceType |
      |resource_manager/cloud_formation_templates/AsgCfnTemplate.yml         |ON_DEMAND   |t2.small     |
    When alarm "compute:alarm:asg-cloudwatch-mem-util:2021-04-05" is installed
      |AutoScalingGroupName                               | Threshold | SNSTopicARN                                   | AlarmName          |
      |{{cfn-output:AsgCfnTemplate>AutoScalingGroupName}} | 1         | {{cfn-output:AsgCfnTemplate>AlarmTopicArn}}   | {{cache:AlarmName}}|
    Then assert metrics for all alarms are populated

