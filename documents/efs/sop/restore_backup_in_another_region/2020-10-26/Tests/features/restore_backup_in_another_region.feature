@efs
Feature: SSM automation document to restore backup in another region

  Scenario: Restore backup in another region

    Given  the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                          | ResourceType |
      | resource_manager/cloud_formation_templates/EFSTemplate.yml                                               | ON_DEMAND    |
      | documents/efs/sop/restore_backup_in_another_region/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestoreBackup_2020-10-26" SSM document
    And cache different region name as "DestinationRegionName" "before" SSM automation execution
    And create a backup vault in region as "DestinationVaultArn" "before" SSM automation execution
      | RegionName                             |
      | {{cache:before>DestinationRegionName}} |
    And cache number of recovery points as "NumberOfRecoveryPoints" "before" SSM automation execution
      | BackupVaultName                                       | FileSystemID                      |
      | {{cfn-output:EFSTemplate>BackupVaultSourceName}}      | {{cfn-output:EFSTemplate>EFSID}}  |
    And cache recovery point arn as "RecoveryPointArn" "before" SSM automation execution
      | FileSystemID                     | BackupVaultName                                  |
      | {{cfn-output:EFSTemplate>EFSID}} | {{cfn-output:EFSTemplate>BackupVaultSourceName}} |
    And SSM automation document "Digito-RestoreBackup_2020-10-26" executed
      | FileSystemID                     | CopyJobIAMRoleArn                        | RestoreJobIAMRoleArn                     | BackupVaultSourceName                            | BackupVaultDestinationArn            | RecoveryPointArn                  | AutomationAssumeRole                                                      | DestinationRegionName                  |
      | {{cfn-output:EFSTemplate>EFSID}} | {{cfn-output:EFSTemplate>JobIAMRoleArn}} | {{cfn-output:EFSTemplate>JobIAMRoleArn}} | {{cfn-output:EFSTemplate>BackupVaultSourceName}} | {{cache:before>DestinationVaultArn}} | {{cache:before>RecoveryPointArn}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestoreBackupAssumeRole}} | {{cache:before>DestinationRegionName}} |

    When SSM automation document "Digito-RestoreBackup_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache execution output value of "RestoreBackupJob.RestoreJobId" as "RestoreJobId" after SSM automation execution
      | ExecutionId                | RegionName                             |
      | {{cache:SsmExecutionId>1}} | {{cache:before>DestinationRegionName}} |
    And cache execution output value of "GetDestinationRecoveryPointArn.DestinationRecoveryPointArn" as "DestinationRecoveryPointArn" after SSM automation execution
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache execution output value of "VerifyRestoreJobStatus.RestoredFSArn" as "RestoredFSArn" after SSM automation execution
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache restore job property "$.Status" as "RestoreJobStatus" "after" SSM automation execution
      | RestoreJobId                 | RegionName                             |
      | {{cache:after>RestoreJobId}} | {{cache:before>DestinationRegionName}} |

    Then assert "RestoreJobStatus" at "after" became equal to "COMPLETED"
    And assert EFS fs exists
      | FileSystemARN                 | RegionName                             |
      | {{cache:after>RestoredFSArn}} | {{cache:before>DestinationRegionName}} |
    And tear down created recovery point
      | RecoveryPointArn                  |  BackupVaultName                                      |
      | {{cache:before>RecoveryPointArn}} | {{cfn-output:EFSTemplate>BackupVaultSourceName}}      |
    And tear down created recovery point
      | RecoveryPointArn                             |  BackupVaultArn                       | RegionName                             |
      | {{cache:after>DestinationRecoveryPointArn}}  |  {{cache:before>DestinationVaultArn}} | {{cache:before>DestinationRegionName}} |
    And tear down backup vault
      | VaultArn                              | RegionName                             |
      | {{cache:before>DestinationVaultArn}}  | {{cache:before>DestinationRegionName}} |
    And tear down filesystem by ARN
      | FileSystemARN                        | RegionName                             |
      | {{cache:after>DestinationVaultArn}}  | {{cache:before>DestinationRegionName}} |
    And cache number of recovery points as "NumberOfRecoveryPoints" "after" SSM automation execution
      | BackupVaultName                                       | FileSystemID                      |
      | {{cfn-output:EFSTemplate>BackupVaultDestinationName}} | {{cfn-output:EFSTemplate>EFSID}}  |
    And assert "NumberOfRecoveryPoints" at "before" became equal to "NumberOfRecoveryPoints" at "after"