@s3
Feature: SSM automation document to restore an S3 bucket from a backup bucket

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document to restore an S3 bucket from a backup bucket without approval to clean the restore bucket
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                            | ResourceType |
      | resource_manager/cloud_formation_templates/S3Template.yml                                  | ON_DEMAND    |
      | documents/s3/sop/restore_from_backup/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestoreFromBackup_2020-09-21" SSM document
    And clear the bucket
      | BucketName                                      |
      | {{cfn-output:S3Template>S3BucketToRestoreName}} |
    And put "2" objects into the bucket
      | BucketName                                   |
      | {{cfn-output:S3Template>S3BackupBucketName}} |
    And cache value of number of files as "ExpectedNumberOfFilesToCopy" at the bucket "before" SSM automation execution
      | BucketName                                   |
      | {{cfn-output:S3Template>S3BackupBucketName}} |
    And SSM automation document "Digito-RestoreFromBackup_2020-09-21" executed
      | S3BackupBucketName                           | S3BucketToRestoreName                           | AutomationAssumeRole                                                          | SNSTopicARNForManualApproval           | IAMPrincipalForManualApproval                       | ApproveCleanRestoreBucketAutomatically |
      | {{cfn-output:S3Template>S3BackupBucketName}} | {{cfn-output:S3Template>S3BucketToRestoreName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestoreFromBackupAssumeRole}} | {{cfn-output:S3Template>SNSTopicName}} | {{cfn-output:S3Template>RoleApproveCleanBucketArn}} | true                                   |


    When SSM automation document "Digito-RestoreFromBackup_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache value of number of files as "ActualNumberOfFilesCopied" at the bucket "after" SSM automation execution
      | BucketName                                      |
      | {{cfn-output:S3Template>S3BucketToRestoreName}} |


    Then assert "ExpectedNumberOfFilesToCopy" at "before" became equal to "ActualNumberOfFilesCopied" at "after"
