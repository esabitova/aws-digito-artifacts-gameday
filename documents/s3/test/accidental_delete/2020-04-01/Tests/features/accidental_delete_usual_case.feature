#@s3
Feature: SSM automation document to accidentally delete files in S3 bucket

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document to accidentally delete files in S3 bucket
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                           | ResourceType |
      | resource_manager/cloud_formation_templates/S3Template.yml                                 | ON_DEMAND    |
      | documents/s3/test/accidental_delete/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And cache current user ARN as "UserArn" "before" SSM automation execution
    And put "2" objects into the bucket
      | BucketName                                   |
      | {{cfn-output:S3Template>S3BucketToRestoreName}} |
    And SSM automation document "Digito-AccidentalDelete_2020-04-01" executed
      | S3BucketWhereObjectsWillBeDeletedFrom           | S3BucketToRestoreWhereObjectWillBeCopiedTo   | AutomationAssumeRole                                                         | S3UserErrorAlarmName                                    | SNSTopicARNForManualApproval           | UserWhoWillApproveCleanRestoreBucket | IsRollback | PreviousExecutionId |
      | {{cfn-output:S3Template>S3BucketToRestoreName}} | {{cfn-output:S3Template>S3BackupBucketName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoAccidentalDeleteAssumeRole}} | {{cfn-output:S3Template>Health4xxErrorsCountAlarmName}} | {{cfn-output:S3Template>SNSTopicName}} | {{cache:before>UserArn}}             | false      | ''                  |
#todo    Approve here execution id which is the step of CleanS3BucketWhereObjectsWillBeDeletedFrom
#todo    And cache value of number of files as "NumberOfFilesAfterDeletion" at the bucket "after" SSM automation execution
#todo copy from aws-documents repo    And assert "NumberOfFilesAfterDeletion" at "before" became not equal to "0"
    And get the "object-to-restore-versions.txt" object from bucket "10" times with error
      | BucketName                                      |
      | {{cfn-output:S3Template>S3BucketToRestoreName}} |
    When SSM automation document "Digito-AccidentalDelete_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |