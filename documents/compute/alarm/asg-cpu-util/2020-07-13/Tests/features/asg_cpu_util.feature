@asg @integration @alarm @cpu
Feature: Alarm Setup - ASG CPU Utilization
  Scenario: Lease ASG from resource manager and test attach an alarm from Document
    Given the cached input parameters
      |AlarmName               |
      |  ASGCPUUtilization  |
    And the cloud formation templates as integration test resources
      |CfnTemplatePath                                                       |ResourceType|InstanceType |
      |resource_manager/cloud_formation_templates/AsgCfnTemplate.yml         |ON_DEMAND   |t2.small     |
    When alarm "compute:alarm:asg-cpu-util:2020-07-13" is installed
      |AutoScalingGroupName                               | Threshold | SNSTopicARN                                   | AlarmName          |
      |{{cfn-output:AsgCfnTemplate>AutoScalingGroupName}} | 90        | {{cfn-output:AsgCfnTemplate>AlarmTopicArn}}   | {{cache:AlarmName}}|
    Then assert metrics for all alarms are populated
    And wait until alarm {{cache:AlarmName}} becomes OK within 180 seconds, check every 15 seconds

