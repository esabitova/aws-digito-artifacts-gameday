@efs
Feature: SSM automation document to restore backup in another region

  Scenario: Restore backup in another region
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                          | ResourceType |
      | resource_manager/cloud_formation_templates/EFSTemplate.yml                                               | ON_DEMAND    |
      | documents/efs/sop/restore_backup_in_another_region/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestoreBackup_2020-10-26" SSM document
    And SSM automation document "Digito-RestoreBackup_2020-10-26" executed
      | FileSystemID                     | JobIAMRoleArn                            | RecoveryPointArn                  | AutomationAssumeRole                                                      |
      | {{cfn-output:EFSTemplate>EFSID}} | {{cfn-output:EFSTemplate>JobIAMRoleArn}} | "foo" | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestoreBackupAssumeRole}} |
