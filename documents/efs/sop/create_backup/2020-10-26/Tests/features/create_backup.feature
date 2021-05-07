@efs
Feature: SSM automation document to create backup of EFS

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document to create backup of EFS
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                       | ResourceType |
      | resource_manager/cloud_formation_templates/EFSTemplate.yml                            | ON_DEMAND    |
      | documents/efs/sop/create_backup/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-CreateEfsBackup_2020-10-26" SSM document
    And SSM automation document "Digito-CreateEfsBackup_2020-10-26" executed
      | FileSystemId                     | BackupVaultName                                  | BackupJobIamRoleArn                      | AutomationAssumeRole                                                        |
      | {{cfn-output:EFSTemplate>EFSID}} | {{cfn-output:EFSTemplate>BackupVaultSourceName}} | {{cfn-output:EFSTemplate>JobIAMRoleArn}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoCreateEfsBackupAssumeRole}} |

    When SSM automation document "Digito-CreateEfsBackup_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache execution output value of "CreateBackupJob.RecoveryPointArn" as "RecoveryPointArn" after SSM automation execution
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    Then assert RecoveryPoint fs exists and correct
      | RecoveryPointArn                  |  BackupVaultName                                      | FileSystemId                     |
      | {{cache:after>RecoveryPointArn}}  |  {{cfn-output:EFSTemplate>BackupVaultSourceName}}     | {{cfn-output:EFSTemplate>EFSID}} |
    And tear down created recovery point
      | RecoveryPointArn                  |  BackupVaultName                                  |
      | {{cache:after>RecoveryPointArn}}  |  {{cfn-output:EFSTemplate>BackupVaultSourceName}} |

