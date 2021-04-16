@efs
Feature: SSM automation document to restore backup in another region

  Scenario: Restore backup in another region
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                          | ResourceType |
      | resource_manager/cloud_formation_templates/EFSTemplate.yml                                               | ON_DEMAND    |
      | documents/efs/sop/restore_backup_in_another_region/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestoreBackup_2020-10-26" SSM document
    And cache number of recovery points as "NumberOfRecoveryPoints" "before" SSM automation execution
      | BackupVaultName                                       | FileSystemID                      |
      | {{cfn-output:EFSTemplate>BackupVaultDestinationName}} | {{cfn-output:EFSTemplate>EFSID}}  |
    And cache recovery point arn as "RecoveryPointArn" "before" SSM automation execution
      | FileSystemID                     | BackupVaultName                                        |
      | {{cfn-output:EFSTemplate>EFSID}} | {{cfn-output:EFSTemplate>BackupVaultDestinationName}}  |
    And SSM automation document "Digito-RestoreBackup_2020-10-26" executed
      | FileSystemID                     | JobIAMRoleArn                            | RecoveryPointArn                  | AutomationAssumeRole                                                      |
      | {{cfn-output:EFSTemplate>EFSID}} | {{cfn-output:EFSTemplate>JobIAMRoleArn}} | {{cache:before>RecoveryPointArn}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestoreBackupAssumeRole}} |

    When SSM automation document "Digito-RestoreBackup_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache execution output value of "RestoreBackupJob.RestoreJobId" as "RestoreJobId" after SSM automation execution
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache restore job property "$.Status" as "RestoreJobStatus" "after" SSM automation execution
      | RestoreJobId                 |
      | {{cache:after>RestoreJobId}} |

    Then assert "RestoreJobStatus" at "after" became equal to "COMPLETED"
    And tear down created recovery points and jobs
      | RecoveryPointArn                  |  BackupVaultName                                      |
      | {{cache:before>RecoveryPointArn}} | {{cfn-output:EFSTemplate>BackupVaultDestinationName}} |
    And cache number of recovery points as "NumberOfRecoveryPoints" "after" SSM automation execution
      | BackupVaultName                                       | FileSystemID                      |
      | {{cfn-output:EFSTemplate>BackupVaultDestinationName}} | {{cfn-output:EFSTemplate>EFSID}}  |
    And assert "NumberOfRecoveryPoints" at "before" became equal to "NumberOfRecoveryPoints" at "after"