@s3
Feature: SSM automation document to accidentally delete files in S3 bucket

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document to accidentally delete files in S3 bucket
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                           | ResourceType | CleanupS3BucketLambdaArn                                    |
      | resource_manager/cloud_formation_templates/shared/CleanupS3BucketLambda.yml               | SHARED       |                                                             |
      | resource_manager/cloud_formation_templates/S3Template.yml                                 | ON_DEMAND    |{{cfn-output:CleanupS3BucketLambda>CleanupS3BucketLambdaArn}}|
      | documents/s3/test/accidental_delete/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                                                             |
    And published "Digito-AccidentalDeleteS3Objects_2020-04-01" SSM document
    And clear the bucket
      | BucketName                                   |
      | {{cfn-output:S3Template>S3BackupBucketName}} |
    And put "2" objects into the bucket
      | BucketName                                      |
      | {{cfn-output:S3Template>S3BucketToRestoreName}} |
    And cache value of number of files as "NumberOfFiles" at the bucket "before" SSM automation execution
      | BucketName                                      |
      | {{cfn-output:S3Template>S3BucketToRestoreName}} |
    And SSM automation document "Digito-AccidentalDeleteS3Objects_2020-04-01" executed
      | S3BucketWhereObjectsWillBeDeletedFrom           | S3BucketToRestoreWhereObjectWillBeCopiedTo   | AutomationAssumeRole                                                         | S3UserErrorAlarmName                                    | SNSTopicARNForManualApproval           | IAMPrincipalForManualApproval                       | ForceCleanBucketToRestoreWhereObjectWillBeCopiedTo | IsRollback | PreviousExecutionId |
      | {{cfn-output:S3Template>S3BucketToRestoreName}} | {{cfn-output:S3Template>S3BackupBucketName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoAccidentalDeleteAssumeRole}} | {{cfn-output:S3Template>Health4xxErrorsCountAlarmName}} | {{cfn-output:S3Template>SNSTopicName}} | {{cfn-output:S3Template>RoleApproveCleanBucketArn}} | true                                               | false      | ''                  |

    When Wait for the SSM automation document "Digito-AccidentalDeleteS3Objects_2020-04-01" execution is on step "CleanS3BucketWhereObjectsWillBeDeletedFrom" in status "Success" for "600" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache value of number of files as "ActualNumberOfFiles" at the bucket "after_delete" SSM automation execution
      | BucketName                                   |
      | {{cfn-output:S3Template>S3BucketToRestoreName}} |
#    If we don't trigger the alarm, step has to fail and cause rollback, step and ssm will have TimedOut state
    And Wait for the SSM automation document "Digito-AccidentalDeleteS3Objects_2020-04-01" execution is on step "AssertAlarmToBeRed" in status "TimedOut" for "1200" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And Wait for the SSM automation document "Digito-AccidentalDeleteS3Objects_2020-04-01" execution is on step "RollbackCurrentExecution" in status "Success" for "600" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And get the "0.txt" object from bucket "20" times
      | BucketName                                      |
      | {{cfn-output:S3Template>S3BucketToRestoreName}} |
    And Wait for the SSM automation document "Digito-AccidentalDeleteS3Objects_2020-04-01" execution is on step "AssertAlarmToBeGreen" in status "InProgress" for "600" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And SSM automation document "Digito-AccidentalDeleteS3Objects_2020-04-01" execution in status "TimedOut"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache value of number of files as "ActualNumberOfFiles" at the bucket "after" SSM automation execution
      | BucketName                                   |
      | {{cfn-output:S3Template>S3BackupBucketName}} |

    Then assert "NumberOfFiles" at "before" became not equal to "ActualNumberOfFiles" at "after_delete"
    Then assert "NumberOfFiles" at "before" became equal to "ActualNumberOfFiles" at "after"
    And assert "CheckIsRollback, BackupS3BucketWhereObjectsWillBeDeletedFrom, CleanS3BucketWhereObjectsWillBeDeletedFrom, RollbackCurrentExecution, AssertAlarmToBeGreen" steps are successfully executed in order
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
