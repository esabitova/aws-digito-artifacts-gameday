@dynamodb @integration @alarm
Feature: Alarm Setup - Read Throttle Events Alarm - Green

  Scenario: Alarm is not triggered when read throttle events is less than a threshold - green
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                      | ResourceType |
      | resource_manager/cloud_formation_templates/DynamoDBTemplateWithLimitedThroughput.yml | ON_DEMAND    |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml                   | SHARED       |
    When alarm "dynamodb:alarm:health_read_throttle_events:2020-04-01" is installed
      | alarmId    | Threshold | DynamoDbTable                                                      | SNSTopicARN                       |
      | under_test | 2000      | {{cfn-output:DynamoDBTemplateWithLimitedThroughput>DynamoDBTable}} | {{cfn-output:SnsForAlarms>Topic}} |
    And put random test item and cache it as "TestItem"
      | DynamoDBTableName                                                  |
      | {{cfn-output:DynamoDBTemplateWithLimitedThroughput>DynamoDBTable}} |
    And get test item "TestItem" "200" times
      | DynamoDBTableName                                                  |
      | {{cfn-output:DynamoDBTemplateWithLimitedThroughput>DynamoDBTable}} |
    And sleep for "60" seconds
    And get test item "TestItem" "200" times
      | DynamoDBTableName                                                  |
      | {{cfn-output:DynamoDBTemplateWithLimitedThroughput>DynamoDBTable}} |
    And sleep for "60" seconds
    And get test item "TestItem" "100" times
      | DynamoDBTableName                                                  |
      | {{cfn-output:DynamoDBTemplateWithLimitedThroughput>DynamoDBTable}} |
    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 180 seconds, check every 15 seconds
