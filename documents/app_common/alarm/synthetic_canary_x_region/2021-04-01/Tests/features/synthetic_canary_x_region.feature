@app_common @integration @alarm @synthetics
Feature: Alarm Setup - Application Synthetics Canary - Cross Region
  Scenario: Lease ASG from resource manager and test attach an alarm from Document
    Given the cloud formation templates as integration test resources
      |CfnTemplatePath                                                       |ResourceType|InstanceType |
      |resource_manager/cloud_formation_templates/AsgCfnTemplate.yml         |ON_DEMAND   |t2.small     |
      |resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml    |SHARED      |             |
    When alarm "app_common:alarm:synthetic_canary_x_region:2021-04-01" is installed
      |alarmId    |CanaryName                               | Threshold | SNSTopicARN
      |under_test |{{cfn-output:AsgCfnTemplate>CanaryName}} | 90        | {{cfn-output:SnsForAlarms>Topic}}
    Then assert metrics for all alarms are populated with params
      | CanaryName                               |
      | {{cfn-output:AsgCfnTemplate>CanaryName}} |
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 180 seconds, check every 15 seconds

