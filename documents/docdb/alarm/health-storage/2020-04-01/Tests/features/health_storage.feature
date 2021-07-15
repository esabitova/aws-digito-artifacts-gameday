@docdb @integration @alarm
Feature: Alarm Setup - DocDb Errors
  Scenario: Test DocDb FreeLocalStorage memory:alarm:health-storage:2020-04-01
    Given the cloud formation templates as integration test resources
      |CfnTemplatePath                                                      |ResourceType |
      | resource_manager/cloud_formation_templates/DocDbTemplate.yml        | ON_DEMAND   |
      |resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml   | SHARED      |
    When alarm "docdb:alarm:health-storage:2020-04-01" is installed
      |alarmId    |DBClusterIdentifier                              | Threshold   | SNSTopicARN                       |
      |under_test |{{cfn-output:DocDbTemplate>DBClusterIdentifier}} | 10          | {{cfn-output:SnsForAlarms>Topic}} |
    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 120 seconds, check every 20 seconds

