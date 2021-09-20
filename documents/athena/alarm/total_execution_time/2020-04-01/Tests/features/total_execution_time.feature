@athena @integration @alarm
Feature: Alarm Setup - TotalExecutionTime

  Scenario: Create athena:alarm:total_execution_time:2020-04-01 based on TotalExecutionTime metric and check OK status
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                             | ResourceType | CleanupS3BucketLambdaArn                                      |
      | resource_manager/cloud_formation_templates/shared/CleanupS3BucketLambda.yml | SHARED       |                                                               |
      | resource_manager/cloud_formation_templates/shared/KMS.yml                   | SHARED       |                                                               |
      | resource_manager/cloud_formation_templates/AthenaTemplate.yml               | ON_DEMAND    | {{cfn-output:CleanupS3BucketLambda>CleanupS3BucketLambdaArn}} |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml          | SHARED       |                                                               |
    And the cached input parameters
      | InputFileRelativePath           | InputFileS3Key | InputBucketName                                   |
      | documents/athena/data/input.csv | data/input.csv | {{cfn-output:AthenaTemplate>S3CrawlerBucketName}} |
    And upload file "{{cache:InputFileRelativePath}}" as "{{cache:InputFileS3Key}}" S3 key to S3 bucket with prefix "{{cache:InputBucketName}}" and save locations to "InputCsvFile" cache property
    And run the Crawler for creating table
      | GlueCrawlerName                               |
      | {{cfn-output:AthenaTemplate>GlueCrawlerName}} |
    When alarm "athena:alarm:total_execution_time:2020-04-01" is installed
      | alarmId    | AthenaWorkGroupName                               | SNSTopicARN                       | Threshold | EvaluationPeriods | DatapointsToAlarm |
      | under_test | {{cfn-output:AthenaTemplate>AthenaWorkGroupName}} | {{cfn-output:SnsForAlarms>Topic}} | 1         | 1                 | 1                 |
    And execute DML query
      | Database                                       | BucketName                                       | AthenaWorkGroupName                              | TableName                   |
      | {{cfn-output:AthenaTemplate>GlueDataBaseName}} | {{cfn-output:AthenaTemplate>S3OutputBucketName}} | {{cfn-output:AthenaTemplate>AthenaWorkGroupName} | athena_test_table_input_csv |
    Then assert metrics for all alarms are populated
    And Wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 180 seconds, check every 15 seconds

#  Scenario: Create athena:alarm:total_execution_time:2020-04-01 based on TotalExecutionTime metric and check ALARM status
#    Given the cloud formation templates as integration test resources
#      | CfnTemplatePath                                                             | ResourceType | CleanupS3BucketLambdaArn                                      |
#      | resource_manager/cloud_formation_templates/shared/CleanupS3BucketLambda.yml | SHARED       |                                                               |
#      | resource_manager/cloud_formation_templates/shared/KMS.yml                   | SHARED       |                                                               |
#      | resource_manager/cloud_formation_templates/AthenaTemplate.yml               | ON_DEMAND    | {{cfn-output:CleanupS3BucketLambda>CleanupS3BucketLambdaArn}} |
#      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml          | SHARED       |                                                               |
#    And the cached input parameters
#      | DistributionPackageRelativePath | DistributionPackageS3Key |
#      | documents/athena/data/input.csv | data/input.csv           |
#    And upload file "{{cache:DistributionPackageRelativePath}}" as "{{cache:DistributionPackageS3Key}}" S3 key to S3 bucket with prefix "ssm-docdb-test-resources" and save locations to "CloudWatchCanary" cache property
#      | BucketName                                        |
#      | {{cfn-output:AthenaTemplate>S3CrawlerBucketName}} |
#    And create table for Athena with Crawler
#      | GlueCrawlerName                               |
#      | {{cfn-output:AthenaTemplate>GlueCrawlerName}} |
#    When alarm "athena:alarm:total_execution_time:2020-04-01" is installed
#      | alarmId    | AthenaWorkGroupName                               | SNSTopicARN                       | Threshold | EvaluationPeriods | DatapointsToAlarm |
#      | under_test | {{cfn-output:AthenaTemplate>AthenaWorkGroupName}} | {{cfn-output:SnsForAlarms>Topic}} | 29        | 1                 | 1                 |
#    And execute DML query
#      | Database                                       | BucketName                                       | AthenaWorkGroupName                              |
#      | {{cfn-output:AthenaTemplate>GlueDataBaseName}} | {{cfn-output:AthenaTemplate>S3OutputBucketName}} | {{cfn-output:AthenaTemplate>AthenaWorkGroupName} |
#    Then assert metrics for all alarms are populated
#    And Wait until alarm {{alarm:under_test>AlarmName}} becomes ALARM within 180 seconds, check every 15 seconds
