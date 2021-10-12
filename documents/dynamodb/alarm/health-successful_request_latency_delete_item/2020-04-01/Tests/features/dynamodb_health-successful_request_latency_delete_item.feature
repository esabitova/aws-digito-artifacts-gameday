@dynamodb @integration @alarm
Feature: Alarm Setup - Amazon DynamoDB SuccessfulRequestLatency DeleteItem
  Scenario: Create dynamodb:alarm:health-successful_request_latency_delete_item:2020-04-01 based on SuccessfulRequestLatency and check OK status
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                    | ResourceType
      | resource_manager/cloud_formation_templates/DynamoDBTemplate.yml    | ON_DEMAND
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml | SHARED
    And put random test item "300" times divided by time and cache items as "TestDynamoDBItems"
      | DynamoDBTableName                             |
      | {{cfn-output:DynamoDBTemplate>DynamoDBTable}} |
    When alarm "dynamodb:alarm:health-successful_request_latency_delete_item:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | DynamoDbTable                                 | Threshold | DatapointsToAlarm | EvaluationPeriods |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:DynamoDBTemplate>DynamoDBTable}} | 100       | 1                 | 1                 |
    And get items from cache using key "TestDynamoDBItems" and delete it divided by time from dynamodb table
      | DynamoDBTableName                             |
      | {{cfn-output:DynamoDBTemplate>DynamoDBTable}} |
    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 1200 seconds, check every 15 seconds

  Scenario: Create dynamodb:alarm:health-successful_request_latency_delete_item:2020-04-01 based on SuccessfulRequestLatency and check ALARM status
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                    | ResourceType
      | resource_manager/cloud_formation_templates/DynamoDBTemplate.yml    | ON_DEMAND
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml | SHARED
    And put random test item "300" times divided by time and cache items as "TestDynamoDBItems"
      | DynamoDBTableName                             |
      | {{cfn-output:DynamoDBTemplate>DynamoDBTable}} |
    When alarm "dynamodb:alarm:health-successful_request_latency_delete_item:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | DynamoDbTable                                 | Threshold | DatapointsToAlarm | EvaluationPeriods |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:DynamoDBTemplate>DynamoDBTable}} | 2         | 1                 | 1                 |
    And get items from cache using key "TestDynamoDBItems" and delete it divided by time from dynamodb table
      | DynamoDBTableName                             |
      | {{cfn-output:DynamoDBTemplate>DynamoDBTable}} |
    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes ALARM within 1200 seconds, check every 15 seconds