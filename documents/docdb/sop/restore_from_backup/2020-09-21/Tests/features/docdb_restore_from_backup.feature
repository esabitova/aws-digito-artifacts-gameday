@docdb
Feature: SSM automation document to recover the database into a known good state.

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document to recover the database into a known good state
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                               | ResourceType |
      | resource_manager/cloud_formation_templates/DocDbTemplate.yml                                  | ON_DEMAND    |
      | documents/docdb/sop/restore_from_backup/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-DocDbRestoreFromBackup_2020-09-21" SSM document

    When SSM automation document "Digito-DocDbRestoreFromBackup_2020-09-21" executed
      | DBClusterIdentifier                              | AutomationAssumeRole                                                               |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoDocDbRestoreFromBackupAssumeRole}} |
    And Wait for the SSM automation document "Digito-DocDbRestoreFromBackup_2020-09-21" execution is on step "WaitUntilRestoredInstancesAvailable" in status "Success" for "1200" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    Then SSM automation document "Digito-DocDbRestoreFromBackup_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |