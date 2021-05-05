@asg @integration @alarm @cpu
Feature: Alarm Setup - ASG Many Unhealthy Hosts
  Scenario: Lease ASG from resource manager and test attach an alarm from Document
    Given the cached input parameters
      |AlarmName                |
      |  ASGManyUnhealthHosts   |
    And the cloud formation templates as integration test resources
      |CfnTemplatePath                                                       |ResourceType|InstanceType |
      |resource_manager/cloud_formation_templates/AsgCfnTemplate.yml         |ON_DEMAND   |t2.small     |
      |resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml    |SHARED      |             |
    When alarm "compute:alarm:asg-many-unhealthy-hosts:2020-07-13" is installed
      |LoadBalancer                               | TargetGroup                                           |Threshold | SNSTopicARN                       | AlarmName          | AlarmLogicalId      |
      |{{cfn-output:AsgCfnTemplate>LoadBalancer}} | {{cfn-output:AsgCfnTemplate>LoadBalancerTargetGroup}} |   0      | {{cfn-output:SnsForAlarms>Topic}} | {{cache:AlarmName}}| {{cache:AlarmName}} |
    Then assert metrics for all alarms are populated
    And wait until alarm {{cache:AlarmName}} becomes OK within 180 seconds, check every 15 seconds

