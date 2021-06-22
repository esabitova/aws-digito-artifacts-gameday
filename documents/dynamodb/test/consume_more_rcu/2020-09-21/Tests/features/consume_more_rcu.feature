@dynamodb
Feature: SSM automation document to test dynamodb read throttling

  Scenario: Test that alarm detects when DynamoDB has read throttling events
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                 | ResourceType |
      | resource_manager/cloud_formation_templates/dedicated/DynamoDBTemplateWithProvisionedBilling.yml | DEDICATED    |
      | documents/dynamodb/test/consume_more_rcu/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml  | ASSUME_ROLE  |
    And published "Digito-ConsumeMoreRCU_2020-09-21" SSM document
    And cache table property "$.Table.ProvisionedThroughput.ReadCapacityUnits" as "ReadCapacityUnits" "before" SSM automation execution
      | TableName                                                           |
      | {{cfn-output:DynamoDBTemplateWithProvisionedBilling>DynamoDBTable}} |
    And put random test item and cache it as "TestItem"
      | DynamoDBTableName                                                   |
      | {{cfn-output:DynamoDBTemplateWithProvisionedBilling>DynamoDBTable}} |

    When SSM automation document "Digito-ConsumeMoreRCU_2020-09-21" executed
      | DynamoDBTableName                                                   | AutomationAssumeRole                                                               | ReadThrottleAlarmName                                                             | ReadCapacityUnitsLimit |
      | {{cfn-output:DynamoDBTemplateWithProvisionedBilling>DynamoDBTable}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestoreFromPointInTimeAssumeRole}} | {{cfn-output:DynamoDBTemplateWithProvisionedBilling>ReadThrottleEventsAlarmName}} | 2                      |
    And Wait for the SSM automation document "Digito-ConsumeMoreRCU_2020-09-21" execution is on step "AssertAlarmToBeRed" in status "InProgress" for "1400" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And sleep for "30" seconds
    And get test item "TestItem" "320" times
      | DynamoDBTableName                                                   |
      | {{cfn-output:DynamoDBTemplateWithProvisionedBilling>DynamoDBTable}} |
    And sleep for "60" seconds
    And get test item "TestItem" "320" times
      | DynamoDBTableName                                                   |
      | {{cfn-output:DynamoDBTemplateWithProvisionedBilling>DynamoDBTable}} |
    And sleep for "60" seconds
    And get test item "TestItem" "320" times
      | DynamoDBTableName                                                   |
      | {{cfn-output:DynamoDBTemplateWithProvisionedBilling>DynamoDBTable}} |

    And Wait for the SSM automation document "Digito-ConsumeMoreRCU_2020-09-21" execution is on step "AssertAlarmToBeGreen" in status "InProgress" for "1400" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And sleep for "60" seconds
    And get test item "TestItem" "320" times
      | DynamoDBTableName                                                   |
      | {{cfn-output:DynamoDBTemplateWithProvisionedBilling>DynamoDBTable}} |
    And sleep for "60" seconds
    And get test item "TestItem" "320" times
      | DynamoDBTableName                                                   |
      | {{cfn-output:DynamoDBTemplateWithProvisionedBilling>DynamoDBTable}} |
    And sleep for "60" seconds
    And get test item "TestItem" "320" times
      | DynamoDBTableName                                                   |
      | {{cfn-output:DynamoDBTemplateWithProvisionedBilling>DynamoDBTable}} |

    Then SSM automation document "Digito-ConsumeMoreRCU_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache table property "$.Table.ProvisionedThroughput.ReadCapacityUnits" as "ReadCapacityUnits" "after" SSM automation execution
      | TableName                                                           |
      | {{cfn-output:DynamoDBTemplateWithProvisionedBilling>DynamoDBTable}} |
    And assert "ReadCapacityUnits" at "before" became equal to "ReadCapacityUnits" at "after"
