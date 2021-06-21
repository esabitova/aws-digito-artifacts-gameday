@dynamodb @integration @alarm @write_throttle
Feature: Alarm Setup - Write Throttle Events Alarm
  Scenario: Reports when write throttle events is less than a threshold
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                  | ResourceType |
      | resource_manager/cloud_formation_templates/DynamoDBTemplate.yml                                  | ON_DEMAND    |
      | documents/dynamodb/sop/restore_from_backup/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml                               | SHARED       |
    When alarm "dynamodb:alarm:health_write_throttle_events:2020-04-01" is installed
      | alarmId    | Threshold | DynamoDbTable                                 | SNSTopicARN |
      | under_test | 1         | {{cfn-output:DynamoDBTemplate>DynamoDBTable}} | {{cfn-output:SnsForAlarms>Topic}}    |
#    Then assert metrics for all alarms are populated
#    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 180 seconds, check every 15 seconds
