@dynamodb @integration @alarm
Feature: Alarm Setup - conditional check failed requests
  Scenario: Alarm is not triggered when amount of conditional check failed requests is less than threshold - green
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                 | ResourceType |
      | resource_manager/cloud_formation_templates/dedicated/DynamoDBTemplateWithProvisionedBilling.yml | ON_DEMAND    |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml                              | SHARED       |
    When alarm "dynamodb:alarm:health_conditional_check_failed_requests:2020-04-01" is installed
      | alarmId    | Threshold | DynamoDbTable                                                       | SNSTopicARN                       |
      | under_test | 1         | {{cfn-output:DynamoDBTemplateWithProvisionedBilling>DynamoDBTable}} | {{cfn-output:SnsForAlarms>Topic}} |

    Then wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 180 seconds, check every 15 seconds

  Scenario: Reports when amount of conditional check failed requests is greater than or equal to threshold - red
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                 | ResourceType |
      | resource_manager/cloud_formation_templates/dedicated/DynamoDBTemplateWithProvisionedBilling.yml | ON_DEMAND    |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml                              | SHARED       |
    When alarm "dynamodb:alarm:health_conditional_check_failed_requests:2020-04-01" is installed
      | alarmId    | Threshold | DynamoDbTable                                                       | SNSTopicARN                       |
      | under_test | 1         | {{cfn-output:DynamoDBTemplateWithProvisionedBilling>DynamoDBTable}} | {{cfn-output:SnsForAlarms>Topic}} |
    And put random test item and cache it as "TestItem"
      | DynamoDBTableName                                                   |
      | {{cfn-output:DynamoDBTemplateWithProvisionedBilling>DynamoDBTable}} |
    And put random test item "300" times with condition "userId = fooId"
      | DynamoDBTableName                                                  |
      | {{cfn-output:DynamoDBTemplateWithProvisionedBilling>DynamoDBTable}} |
    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes ALARM within 250 seconds, check every 15 seconds
