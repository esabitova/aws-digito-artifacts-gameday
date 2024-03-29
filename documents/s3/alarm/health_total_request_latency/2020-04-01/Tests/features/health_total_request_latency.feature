@s3 @integration @alarm
Feature: Alarm Setup - TotalRequestLatency

  Scenario: Create the alarm based on the TotalRequestLatency metric
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                             | ResourceType | CleanupS3BucketLambdaArn                                    |
      | resource_manager/cloud_formation_templates/shared/CleanupS3BucketLambda.yml | SHARED       |                                                             |
      | resource_manager/cloud_formation_templates/S3Template.yml                   | ON_DEMAND    |{{cfn-output:CleanupS3BucketLambda>CleanupS3BucketLambdaArn}}|
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml          | SHARED       |                                                             |
    When alarm "s3:alarm:health_total_request_latency:2020-04-01" is installed
      | alarmId    | S3BucketName                                    | Threshold | SNSTopicARN                       |
      | under_test | {{cfn-output:S3Template>S3BucketToRestoreName}} | 2000      | {{cfn-output:SnsForAlarms>Topic}} |
    And put "1" objects into the bucket
      | BucketName                                      |
      | {{cfn-output:S3Template>S3BucketToRestoreName}} |
    # Skip asserts since S3 request based metrics have huge delay even more than 1 hour
