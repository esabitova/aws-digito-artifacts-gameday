@dynamodb @integration @alarm @write_throttle
Feature: Alarm Setup - Write Throttle Events Alarm
  Scenario: Reports when write throttle events is less than a threshold
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                          | ResourceType |
      | resource_manager/cloud_formation_templates/DynamoDBTemplate.yml                                          | ON_DEMAND    |
      | documents/dynamodb/sop/update_provisioned_capacity/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml                                       | SHARED       |
    And published "Digito-UpdateProvisionedCapacity_2020-04-01" SSM document
    When alarm "dynamodb:alarm:health_write_throttle_events:2020-04-01" is installed
      | alarmId    | Threshold | DynamoDbTable                                 | SNSTopicARN                       |
      | under_test | 1         | {{cfn-output:DynamoDBTemplate>DynamoDBTable}} | {{cfn-output:SnsForAlarms>Topic}} |
    And cache table property "$.Table.ProvisionedThroughput.ReadCapacityUnits" as "ActualReadCapacityUnits" "before" SSM automation execution
      | TableName                                     |
      | {{cfn-output:DynamoDBTemplate>DynamoDBTable}} |
    And cache table property "$.Table.ProvisionedThroughput.WriteCapacityUnits" as "OldWriteCapacityUnits" "before" SSM automation execution
      | TableName                                     |
      | {{cfn-output:DynamoDBTemplate>DynamoDBTable}} |
    And SSM automation document "Digito-UpdateProvisionedCapacity_2020-04-01" executed
      | DynamoDBTableName                             | DynamoDBTableRCU                         | DynamoDBTableWCU | AutomationAssumeRole                                                                  |
      | {{cfn-output:DynamoDBTemplate>DynamoDBTable}} | {{cache:before>ActualReadCapacityUnits}} | 0                | {{cfn-output:AutomationAssumeRoleTemplate>DigitoUpdateProvisionedCapacityAssumeRole}} |
    # putItem
    And put random test item and cache it as "TestItem"
      | DynamoDBTableName                             |
      | {{cfn-output:DynamoDBTemplate>DynamoDBTable}} |

    Then assert metrics for all alarms are populated
    And put random test item and cache it as "TestItem"
      | DynamoDBTableName                             |
      | {{cfn-output:DynamoDBTemplate>DynamoDBTable}} |
    And put random test item and cache it as "TestItem"
      | DynamoDBTableName                             |
      | {{cfn-output:DynamoDBTemplate>DynamoDBTable}} |
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 180 seconds, check every 15 seconds
    # rollback
    And SSM automation document "Digito-UpdateProvisionedCapacity_2020-04-01" executed
      | DynamoDBTableName                             | DynamoDBTableRCU                         | DynamoDBTableWCU                       | AutomationAssumeRole                                                                  |
      | {{cfn-output:DynamoDBTemplate>DynamoDBTable}} | {{cache:before>ActualReadCapacityUnits}} | {{cache:before>OldWriteCapacityUnits}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoUpdateProvisionedCapacityAssumeRole}} |
