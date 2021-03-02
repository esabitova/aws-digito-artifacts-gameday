@s3
Feature: SSM automation document to restore an S3 bucket from a backup bucket

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document to restore an S3 bucket from a backup bucket with an approval to clean the restore bucket
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                            | ResourceType |
      | resource_manager/cloud_formation_templates/S3Template.yml                                  | ON_DEMAND    |
      | documents/s3/sop/restore_from_backup/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And clear the bucket
      | BucketName                                      |
      | {{cfn-output:S3Template>S3BucketToRestoreName}} |
    And put "1" objects into the bucket
      | BucketName                                      |
      | {{cfn-output:S3Template>S3BucketToRestoreName}} |
    And put "2" objects into the bucket
      | BucketName                                   |
      | {{cfn-output:S3Template>S3BackupBucketName}} |
    And cache value of number of files as "ExpectedNumberOfFilesToCopy" at the bucket "before" SSM automation execution
      | BucketName                                   |
      | {{cfn-output:S3Template>S3BackupBucketName}} |
    And cache current user ARN as "UserArn" at the bucket "before" SSM automation execution
    And SSM automation document "Digito-RestoreFromBackup_2020-09-21" executed
      | S3BackupBucketName                           | S3BucketToRestoreName                           | AutomationAssumeRole                                                          | SNSTopicARNForManualApproval           | UserWhoWillApproveCleanRestoreBucket |
      | {{cfn-output:S3Template>S3BackupBucketName}} | {{cfn-output:S3Template>S3BucketToRestoreName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestoreFromBackupAssumeRole}} | {{cfn-output:S3Template>SNSTopicName}} | {{cache:before>UserArn}}             |

    When Wait for SSM automation document "Digito-RestoreFromBackup_2020-09-21" execution is on step "ApproveCleanRestoreBucketOrCancel" in status "Waiting" for "180" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And Approve SSM automation document
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And SSM automation document "Digito-RestoreFromBackup_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache value of number of files as "ActualNumberOfFilesCopied" at the bucket "after" SSM automation execution
      | BucketName                                      |
      | {{cfn-output:S3Template>S3BucketToRestoreName}} |


    Then assert "ExpectedNumberOfFilesToCopy" at "before" became equal to "ActualNumberOfFilesCopied" at "after"
