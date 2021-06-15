@s3 @restore_from_backup
Feature: SSM automation document to restore an S3 object into previous version

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document to restore an S3 object into previous version
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                     | ResourceType |CleanupS3BucketLambdaArn                                     |
      | resource_manager/cloud_formation_templates/shared/CleanupS3BucketLambda.yml                         | SHARED       |                                                             |
      | resource_manager/cloud_formation_templates/S3Template.yml                                           | ON_DEMAND    |{{cfn-output:CleanupS3BucketLambda>CleanupS3BucketLambdaArn}}|
      | documents/s3/sop/restore_to_previous_versions/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                                                             |
    And published "Digito-RestoringToPreviousVersion_2020-09-21" SSM document
    And put "object-to-restore-version.txt" object "2" times with different content into "S3Bucket" bucket
      | S3Bucket                                        |
      | {{cfn-output:S3Template>S3BucketToRestoreName}} |
    And cache value of "previous" version of the "object-to-restore-version.txt" file as "OldPreviousVersion" at "S3Bucket" bucket "before" SSM automation execution
      | S3Bucket                                        |
      | {{cfn-output:S3Template>S3BucketToRestoreName}} |
    And cache value of "ETag" property of the "object-to-restore-version.txt" file with the specific "VersionId" version as "OldPreviousVersionObjectHash" at "S3Bucket" bucket "before" SSM automation execution
      | S3Bucket                                        | VersionId                           |
      | {{cfn-output:S3Template>S3BucketToRestoreName}} | {{cache:before>OldPreviousVersion}} |
    And cache value of "latest" version of the "object-to-restore-version.txt" file as "OldLastVersion" at "S3Bucket" bucket "before" SSM automation execution
      | S3Bucket                                        |
      | {{cfn-output:S3Template>S3BucketToRestoreName}} |
    And SSM automation document "Digito-RestoringToPreviousVersion_2020-09-21" executed
      | S3BucketName                                    | S3BucketObjectKey             | AutomationAssumeRole                                                                   |
      | {{cfn-output:S3Template>S3BucketToRestoreName}} | object-to-restore-version.txt | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestoringToPreviousVersionAssumeRole}} |

    When SSM automation document "Digito-RestoringToPreviousVersion_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache value of "latest" version of the "object-to-restore-version.txt" file as "ActualLastVersion" at "S3Bucket" bucket "after" SSM automation execution
      | S3Bucket                                        |
      | {{cfn-output:S3Template>S3BucketToRestoreName}} |
    And cache value of "ETag" property of the "object-to-restore-version.txt" file with the specific "VersionId" version as "ActualLastVersionObjectHash" at "S3Bucket" bucket "after" SSM automation execution
      | S3Bucket                                        | VersionId                         |
      | {{cfn-output:S3Template>S3BucketToRestoreName}} | {{cache:after>ActualLastVersion}} |


    Then assert "OldLastVersion" at "before" became not equal to "ActualLastVersion" at "after"
    Then assert "OldPreviousVersionObjectHash" at "before" became equal to "ActualLastVersionObjectHash" at "after"
