@dynamodb
Feature: SSM automation document to restore the database from point in time.

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document to restore the database to point in time
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                       | ResourceType |
      | resource_manager/cloud_formation_templates/DynamoDBTemplate.yml                                       | ON_DEMAND    |
      | documents/dynamodb/sop/restore_to_point_in_time/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestoreToPointInTime_2020-04-01" SSM document

    When SSM automation document "Digito-RestoreToPointInTime_2020-04-01" executed
      | DynamoDBTableSourceName                       | DynamoDBTableTargetName | AutomationAssumeRole                                                               |
      | {{cfn-output:DynamoDBTemplate>DynamoDBTable}} | TargetTable             | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestoreFromPointInTimeAssumeRole}} |

    Then SSM automation document "Digito-RestoreToPointInTime_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
