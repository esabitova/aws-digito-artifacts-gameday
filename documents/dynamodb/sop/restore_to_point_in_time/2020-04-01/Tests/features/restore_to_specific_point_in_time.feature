@dynamodb
Feature: SSM automation document to restore the database from point in time.

  Scenario: Restores table to the specific point
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                       | ResourceType |
      | resource_manager/cloud_formation_templates/DynamoDBTemplate.yml                                       | ON_DEMAND    |
      | documents/dynamodb/sop/restore_to_point_in_time/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestoreToPointInTime_2020-04-01" SSM document
    And the cached input parameters
      | TargetTableToRestoreName |
      | TargetTableToRestore     |
    And valid recovery point in time for {{cfn-output:DynamoDBTemplate>DynamoDBTable}} and cache it as ValidRecoveryPoint
    And Drop Dynamo DB table with the name {{cache:TargetTableToRestoreName}} and wait for 300 seconds with interval 20 seconds
    When SSM automation document "Digito-RestoreToPointInTime_2020-04-01" executed
      | DynamoDBTableSourceName                       | DynamoDBTableTargetName            | AutomationAssumeRole                                                               | RecoveryPointDateTime        |
      | {{cfn-output:DynamoDBTemplate>DynamoDBTable}} | {{cache:TargetTableToRestoreName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestoreFromPointInTimeAssumeRole}} | {{cache:ValidRecoveryPoint}} |

    Then SSM automation document "Digito-RestoreToPointInTime_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And Drop Dynamo DB table with the name {{cache:TargetTableToRestoreName}} and wait for 300 seconds with interval 20 seconds

