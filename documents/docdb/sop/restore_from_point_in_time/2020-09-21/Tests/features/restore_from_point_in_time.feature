@docdb
Feature: SSM automation document to recover the database into a known good state.

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                              | ResourceType |
      | resource_manager/cloud_formation_templates/DocDbTemplate.yml                                 | ON_DEMAND    |
      | documents/docdb/sop/restore_from_point_in_time/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestoreFromPointInTime_2020-09-21" SSM document
    When SSM automation document "Digito-RestoreFromPointInTime_2020-09-21" executed
      | DBClusterIdentifier                              | AutomationAssumeRole                                                               |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestoreFromPointInTimeAssumeRole}} |

    Then SSM automation document "Digito-RestoreFromPointInTime_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |