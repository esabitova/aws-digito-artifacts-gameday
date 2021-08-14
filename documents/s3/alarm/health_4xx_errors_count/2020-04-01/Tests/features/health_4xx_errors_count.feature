@s3 @integration @alarm
Feature: Alarm Setup - S3 Bucket 4xx Errors
  Scenario: Create the alarm based on the 4xxErrors metric
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                             | ResourceType | CleanupS3BucketLambdaArn                                      |
      | resource_manager/cloud_formation_templates/shared/CleanupS3BucketLambda.yml | SHARED       |                                                               |
      | resource_manager/cloud_formation_templates/S3Template.yml                   | ON_DEMAND    | {{cfn-output:CleanupS3BucketLambda>CleanupS3BucketLambdaArn}} |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml          | SHARED       |                                                               |
    When alarm "s3:alarm:health_4xx_errors_count:2020-04-01" is installed
      | alarmId    | S3BucketName                                    | Threshold | SNSTopicARN                       |
      | under_test | {{cfn-output:S3Template>S3BucketToRestoreName}} | 0         | {{cfn-output:SnsForAlarms>Topic}} |
    And put "1" objects into the bucket
      | BucketName                                      |
      | {{cfn-output:S3Template>S3BucketToRestoreName}} |
    And get the "0.txt" object from bucket "5" times
      | BucketName                                      |
      | {{cfn-output:S3Template>S3BucketToRestoreName}} |
    # Since it is the request metric it occurs after huge delay
    Then assert metrics for all alarms are populated within 1200 seconds, check every 15 seconds
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 1200 seconds, check every 15 seconds