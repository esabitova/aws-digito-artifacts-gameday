@s3 @integration @alarm
Feature: Alarm Setup - S3 Bucket 5xx Errors

  Scenario: Create the alarm based on the 5xxErrors metric
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                    | ResourceType |
      | resource_manager/cloud_formation_templates/S3Template.yml          | ON_DEMAND    |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml | SHARED       |
    When alarm "s3:alarm:health_5xx_errors_count:2020-04-01" is installed
      | alarmId    | S3BucketName                                    | Threshold | SNSTopicARN                       |
      | under_test | {{cfn-output:S3Template>S3BucketToRestoreName}} | 0         | {{cfn-output:SnsForAlarms>Topic}} |