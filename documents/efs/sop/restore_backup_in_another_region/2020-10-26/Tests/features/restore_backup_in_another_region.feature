@efs
Feature: SSM automation document to restore backup in another region

  Scenario: Restore backup in another region
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                          | ResourceType |
      | resource_manager/cloud_formation_templates/EFSTemplate.yml                                               | ON_DEMAND    |
      | documents/efs/sop/restore_backup_in_another_region/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And cache recovery point arn as "RecoveryPointArn"
      | BackupVaultName                                  |
      | {{cfn-output:EFSTemplate>BackupVaultSourceName}} |
    And SSM automation document "Digito-RestoreBackup" executed
      | FileSystemID                     | JobIAMRoleArn                            | RecoveryPointArn                  | AutomationAssumeRole                                                      |
      | {{cfn-output:EFSTemplate>EFSID}} | {{cfn-output:EFSTemplate>JobIAMRoleArn}} | {{cache:before>RecoveryPointArn}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestoreBackupAssumeRole}} |

    When SSM automation document "Digito-RestoreBackup" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache execution output value of "restoreBackupJob.RestoreJobId" as "RestoreJobId" after SSM automation execution
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache restore job property of "Status" as "RestoreJobStatus" "after" SSM automation execution
      | RestoreJobId                 |
      | {{cache:after>RestoreJobId}} |

    Then assert "RestoreJobStatus" at "after" became equal to "COMPLETED"