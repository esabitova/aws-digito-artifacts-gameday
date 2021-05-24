@efs @integration @alarm
Feature: Alarm Setup - EFS ClientConnections
  Scenario: Lease EFS from resource manager and test attach an alarm from Document
    Given the cloud formation templates as integration test resources
      |CfnTemplatePath                                                    | ResourceType
      |resource_manager/cloud_formation_templates/EFSTemplate.yml         | ON_DEMAND
      |resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml | SHARED
    When alarm "efs:alarm:percent_io_limit:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       |FileSystem                       | Threshold  | MaxTimeMinutes |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} |{{cfn-output:EFSTemplate>EFSID}} | 90         | 3              |
    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 180 seconds, check every 15 seconds