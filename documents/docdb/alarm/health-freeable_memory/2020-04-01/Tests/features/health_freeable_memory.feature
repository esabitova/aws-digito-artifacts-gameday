@docdb @integration @alarm
Feature: Alarm Setup - DocDb Errors
  Scenario: Test DocDb freeable memory:alarm:health-freeable_memory:2020-04-01
    Given the cloud formation templates as integration test resources
      |CfnTemplatePath                                                      |ResourceType |
      | resource_manager/cloud_formation_templates/DocDbTemplate.yml        | ON_DEMAND   |
      |resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml   | SHARED      |
    When alarm "docdb:alarm:health-freeable_memory:2020-04-01" is installed
      |alarmId    |DBInstancePrimaryIdentifier                              | Threshold   | SNSTopicARN                       |
      |under_test |{{cfn-output:DocDbTemplate>DBInstancePrimaryIdentifier}} | 157286400   | {{cfn-output:SnsForAlarms>Topic}} |
    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 120 seconds, check every 20 seconds

