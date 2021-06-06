@asg_clb @integration @alarm @multiple_unhealthy
Feature: Alarm Setup - ASG Multiple dying hosts CLB
  Scenario: Lease ASG from resource manager and test attach an alarm from Document
    Given the cloud formation templates as integration test resources
      |CfnTemplatePath                                                       |ResourceType|InstanceType |
      |resource_manager/cloud_formation_templates/AsgClbCfnTemplate.yml      |ON_DEMAND   |t2.small     |
      |resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml    |SHARED      |             |
    When alarm "compute:alarm:asg-multiple-unhealthy-hosts-clb:2020-07-13" is installed
      |alarmId    |LoadBalancer                                  |Threshold | SNSTopicARN
      |under_test |{{cfn-output:AsgClbCfnTemplate>LoadBalancer}} |   0      | {{cfn-output:SnsForAlarms>Topic}}
    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 180 seconds, check every 15 seconds
