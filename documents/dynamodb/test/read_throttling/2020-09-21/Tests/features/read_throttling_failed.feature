@dynamodb
Feature: SSM automation document to test dynamodb read throttling

  Scenario: Execute SSM automation document Digito-ForceDynamoDBTableReadThrottlingTest_2020-09-21 to test failure case
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                 | ResourceType |
      | resource_manager/cloud_formation_templates/dedicated/DynamoDBTemplateWithProvisionedBilling.yml | DEDICATED    |
      | documents/dynamodb/test/read_throttling/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml   | ASSUME_ROLE  |
    And published "Digito-ForceDynamoDBTableReadThrottlingTest_2020-09-21" SSM document
    And cache table property "$.Table.ProvisionedThroughput.ReadCapacityUnits" as "ReadCapacityUnits" "before" SSM automation execution
      | TableName                                                           |
      | {{cfn-output:DynamoDBTemplateWithProvisionedBilling>DynamoDBTable}} |

    When SSM automation document "Digito-ForceDynamoDBTableReadThrottlingTest_2020-09-21" executed
      | DynamoDBTableName                                                   | AutomationAssumeRole                                                                             | ReadThrottleAlarmName                                                             | ReadCapacityUnitsLimit |
      | {{cfn-output:DynamoDBTemplateWithProvisionedBilling>DynamoDBTable}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoForceDynamoDBTableReadThrottlingTestAssumeRole}} | {{cfn-output:DynamoDBTemplateWithProvisionedBilling>ReadThrottleEventsAlarmName}} | 2                      |
    # Timeouts if no consumption is applied
    And Wait for the SSM automation document "Digito-ForceDynamoDBTableReadThrottlingTest_2020-09-21" execution is on step "AssertAlarmToBeRed" in status "TimedOut" for "1400" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    Then Wait for the SSM automation document "Digito-ForceDynamoDBTableReadThrottlingTest_2020-09-21" execution is on step "AssertAlarmToBeGreen" in status "Success" for "1400" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And SSM automation document "Digito-ForceDynamoDBTableReadThrottlingTest_2020-09-21" execution in status "TimedOut"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache table property "$.Table.ProvisionedThroughput.ReadCapacityUnits" as "ReadCapacityUnits" "after" SSM automation execution
      | TableName                                                           |
      | {{cfn-output:DynamoDBTemplateWithProvisionedBilling>DynamoDBTable}} |
    And assert "ReadCapacityUnits" at "before" became equal to "ReadCapacityUnits" at "after"
