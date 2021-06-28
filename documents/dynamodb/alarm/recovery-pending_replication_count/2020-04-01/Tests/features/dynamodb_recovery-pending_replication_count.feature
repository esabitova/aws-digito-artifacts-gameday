@dynamodb @integration @alarm
Feature: Alarm Setup - dynamodb PendingReplicationCount
  Scenario: pending_replication_count - green
    Given the cloud formation templates as integration test resources
      |CfnTemplatePath                                                    | ResourceType
      |resource_manager/cloud_formation_templates/DynamoDBTemplate.yml    | ON_DEMAND
      |resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml | SHARED
    And cache different region name as "GlobalTableSecondaryRegion" "before" SSM automation execution
    And enabled global dynamodb table {{cfn-output:DynamoDBTemplate>DynamoDBTable}} in the region {{cache:before>GlobalTableSecondaryRegion}} and wait for 1200 seconds with delay 20 seconds

    When alarm "dynamodb:alarm:recovery-pending_replication_count:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       |DynamoDbTable                                 | Region                                     | Threshold |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} |{{cfn-output:DynamoDBTemplate>DynamoDBTable}} | {{cache:before>GlobalTableSecondaryRegion}}| 100      |
    And put random test items until alarm {{alarm:under_test>AlarmName}} becomes OK for 600 seconds, check every 15 seconds
      | DynamoDBTableName                             |
      | {{cfn-output:DynamoDBTemplate>DynamoDBTable}} |
