@efs
Feature: SSM automation document to create backup of EFS

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document to create backup of EFS
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                       | ResourceType |
      | resource_manager/cloud_formation_templates/EFSTemplate.yml                            | ON_DEMAND    |
      | documents/efs/sop/create_backup/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-CreateBackup_2020-10-26" SSM document
    And SSM automation document "Digito-CreateBackup_2020-10-26" executed
      | FileSystemId                     | BackupVaultName                                  | BackupJobIamRoleArn                      | AutomationAssumeRole                                                     |
      | {{cfn-output:EFSTemplate>EFSID}} | {{cfn-output:EFSTemplate>BackupVaultSourceName}} | {{cfn-output:EFSTemplate>JobIAMRoleArn}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoCreateBackupAssumeRole}} |
    And SSM automation document "Digito-CreateBackup_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
