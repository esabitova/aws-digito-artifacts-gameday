@athena @integration @alarm
Feature: Alarm Setup - TotalExecutionTime_QueryState_Failed
  Scenario: Create athena:alarm:total_execution_time_failed:2020-04-01 based on TotalExecutionTime metric and check OK status
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                             | ResourceType | CleanupS3BucketLambdaArn                                      |
      | resource_manager/cloud_formation_templates/shared/CleanupS3BucketLambda.yml | SHARED       |                                                               |
      | resource_manager/cloud_formation_templates/shared/KMS.yml                   | SHARED       |                                                               |
      | resource_manager/cloud_formation_templates/AthenaTemplate.yml               | ON_DEMAND    | {{cfn-output:CleanupS3BucketLambda>CleanupS3BucketLambdaArn}} |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml          | SHARED       |                                                               |
    And upload csv files to S3 bucket for Crawler
      | BucketName                                        |
      | {{cfn-output:AthenaTemplate>S3CrawlerBucketName}} |
    And create table for Athena with Crawler
    When alarm "athena:alarm:total_execution_time:2020-04-01" is installed
      | alarmId    | AthenaWorkGroupName                               | SNSTopicARN                       | Threshold | EvaluationPeriods | DatapointsToAlarm |
      | under_test | {{cfn-output:AthenaTemplate>AthenaWorkGroupName}} | {{cfn-output:SnsForAlarms>Topic}} | 1        | 1                 | 1                 |
    And execute DML query
    Then assert metrics for all alarms are populated
    And Wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 180 seconds, check every 15 seconds

  Scenario: Create athena:alarm:total_execution_time_failed:2020-04-01 based on TotalExecutionTime metric and check ALARM status
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                             | ResourceType | CleanupS3BucketLambdaArn                                      |
      | resource_manager/cloud_formation_templates/shared/CleanupS3BucketLambda.yml | SHARED       |                                                               |
      | resource_manager/cloud_formation_templates/shared/KMS.yml                   | SHARED       |                                                               |
      | resource_manager/cloud_formation_templates/AthenaTemplate.yml               | ON_DEMAND    | {{cfn-output:CleanupS3BucketLambda>CleanupS3BucketLambdaArn}} |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml          | SHARED       |                                                               |
    And upload csv files to S3 bucket for Crawler
      | BucketName                                        |
      | {{cfn-output:AthenaTemplate>S3CrawlerBucketName}} |
    And create table for Athena with Crawler
    When alarm "athena:alarm:total_execution_time:2020-04-01" is installed
      | alarmId    | AthenaWorkGroupName                               | SNSTopicARN                       | Threshold | EvaluationPeriods | DatapointsToAlarm |
      | under_test | {{cfn-output:AthenaTemplate>AthenaWorkGroupName}} | {{cfn-output:SnsForAlarms>Topic}} | 1        | 1                 | 1                 |
    And execute DML query
    Then assert metrics for all alarms are populated
    And Wait until alarm {{alarm:under_test>AlarmName}} becomes ALARM within 180 seconds, check every 15 seconds
