@dynamodb
Feature: SSM automation document to restore the database from point in time.

  Scenario: Restores table to the specific point
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                       | ResourceType |
      | resource_manager/cloud_formation_templates/DynamoDBTemplate.yml                                       | ON_DEMAND    |
      | documents/dynamodb/sop/restore_to_point_in_time/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestoreToPointInTime_2020-04-01" SSM document
    And published "Digito-CopyDynamoDBTablePropertiesUtil_2020-04-01" SSM document
    And generate and cache random string with prefix digito_target_table as TargetTableToRestoreName
    And find a valid recovery point in time for {{cfn-output:DynamoDBTemplate>DynamoDBTable}} and cache it as ValidRecoveryPoint
    And register cleanup steps for table {{cache:TargetTableToRestoreName}} with global table secondary region None
    And wait table {{cfn-output:DynamoDBTemplate>DynamoDBTable}} to be active for 300 seconds with interval 20 seconds
    When SSM automation document "Digito-RestoreToPointInTime_2020-04-01" executed
      | DynamoDBTableSourceName                       | DynamoDBTableTargetName            | AutomationAssumeRole                                                               | RecoveryPointDateTime        |
      | {{cfn-output:DynamoDBTemplate>DynamoDBTable}} | {{cache:TargetTableToRestoreName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoDynamodbRestoreFromPointInTimeAssumeRole}} | {{cache:ValidRecoveryPoint}} |
    Then SSM automation document "Digito-RestoreToPointInTime_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

