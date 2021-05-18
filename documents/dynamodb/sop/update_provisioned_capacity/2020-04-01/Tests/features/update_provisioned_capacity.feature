@dynamodb
Feature: SSM automation document used to update provisioned capacity for DynamoDB Table.

  Scenario: Update provisioned capacity for DynamoDB Table
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                          | ResourceType |
      | resource_manager/cloud_formation_templates/DynamoDBTemplateWithProvisionedBilling.yml                                          | ON_DEMAND    |
      | documents/dynamodb/sop/update_provisioned_capacity/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-UpdateProvisionedCapacity_2020-04-01" SSM document
    And cache table property "$.Table.ProvisionedThroughput.ReadCapacityUnits" as "OldReadCapacityUnits" "before" SSM automation execution
      | TableName                                     |
      | {{cfn-output:DynamoDBTemplateWithProvisionedBilling>DynamoDBTable}} |
    And cache table property "$.Table.ProvisionedThroughput.WriteCapacityUnits" as "OldWriteCapacityUnits" "before" SSM automation execution
      | TableName                                     |
      | {{cfn-output:DynamoDBTemplateWithProvisionedBilling>DynamoDBTable}} |
    And generate different value of "ReadCapacityUnits" than "OldReadCapacityUnits" from "1" to "4" as "ExpectedReadCapacityUnits" "before" SSM automation execution
      | OldReadCapacityUnits                  |
      | {{cache:before>OldReadCapacityUnits}} |
    And generate different value of "WriteCapacityUnits" than "OldWriteCapacityUnits" from "1" to "4" as "ExpectedWriteCapacityUnits" "before" SSM automation execution
      | OldWriteCapacityUnits                  |
      | {{cache:before>OldWriteCapacityUnits}} |
    And SSM automation document "Digito-UpdateProvisionedCapacity_2020-04-01" executed
      | DynamoDBTableName                             | DynamoDBTableRCU                           | DynamoDBTableWCU                            | AutomationAssumeRole                                                                  |
      | {{cfn-output:DynamoDBTemplateWithProvisionedBilling>DynamoDBTable}} | {{cache:before>ExpectedReadCapacityUnits}} | {{cache:before>ExpectedWriteCapacityUnits}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoUpdateProvisionedCapacityAssumeRole}} |

    When SSM automation document "Digito-UpdateProvisionedCapacity_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache table property "$.Table.ProvisionedThroughput.ReadCapacityUnits" as "ActualReadCapacityUnits" "after" SSM automation execution
      | TableName                                     |
      | {{cfn-output:DynamoDBTemplateWithProvisionedBilling>DynamoDBTable}} |
    And cache table property "$.Table.ProvisionedThroughput.WriteCapacityUnits" as "ActualWriteCapacityUnits" "after" SSM automation execution
      | TableName                                     |
      | {{cfn-output:DynamoDBTemplateWithProvisionedBilling>DynamoDBTable}} |

    Then assert "ExpectedReadCapacityUnits" at "before" became equal to "ActualReadCapacityUnits" at "after"
    And assert "ExpectedWriteCapacityUnits" at "before" became equal to "ActualWriteCapacityUnits" at "after"

    And assert "OldReadCapacityUnits" at "before" became not equal to "ActualReadCapacityUnits" at "after"
    And assert "OldWriteCapacityUnits" at "before" became not equal to "ActualWriteCapacityUnits" at "after"