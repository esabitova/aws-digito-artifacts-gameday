@kinesis-analytics @integration @alarm
Feature: Alarm Setup - Kinesis Analytics Errors
  Scenario: Create kinesis:alarm:data_analytics_downtime:2020-04-01 based on downtime metric and check OK status
    Given the cached input parameters
      | FlinkAppRelativePath                                       | FlinkAppS3Key                               | S3KinesisAnalyticsApplicationBucketNamePrefix |
      | resource_manager/executables/flinkapp/python-test-sink.zip | kinesis-analytics-app/python-test-sink.zip  | kda-apache-flink-application-s3               |
    And create S3 bucket and save the bucket name as "S3KinesisAnalyticsApplicationBucketName" to "KinesisAnalytics" cache property
      | S3BucketNamePrefix                                      | S3BucketTeardown |
      | {{cache:S3KinesisAnalyticsApplicationBucketNamePrefix}} | Yes              |
    And upload Kinesis Data Analytics application file to S3 bucket with given key and save locations to "KinesisAnalytics" cache property       
      | S3KinesisAnalyticsApplicationBucketName                            | FlinkAppRelativePath           | FlinkAppS3Key           |
      | {{cache:KinesisAnalytics>S3KinesisAnalyticsApplicationBucketName}} | {{cache:FlinkAppRelativePath}} | {{cache:FlinkAppS3Key}} |
    And the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                | ResourceType | S3FlinkCodeBucket                                                  | FlinkApplicationObjectKey | KmsKey                              |
      | resource_manager/cloud_formation_templates/shared/KMS.yml                      | SHARED       |                                                                    |                           |                                     |
      | resource_manager/cloud_formation_templates/KinesisAnalyticsTemplateFlink.yml   | ON_DEMAND    | {{cache:KinesisAnalytics>S3KinesisAnalyticsApplicationBucketName}} | {{cache:FlinkAppS3Key}}   | {{cfn-output:KMS>EncryptAtRestKey}} |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml             | SHARED       |                                                                    |                           |                                     |
    And cache Kinesis Data Analytics for "Apache Flink" application InputId as KinesisAnalyticsInputId and OutputId as KinesisAnalyticsOutputId "before" SSM automation execution
      | KinesisAnalyticsApplicationName                                                            |
      | {{cfn-output:KinesisAnalyticsTemplateFlink>KinesisAnalyticsApplicationPhysicalResourceId}} |
    And start Kinesis Data Analytics for "Apache Flink" application
      | KinesisAnalyticsAppName                                                                    |
      | {{cfn-output:KinesisAnalyticsTemplateFlink>KinesisAnalyticsApplicationPhysicalResourceId}} |
    When alarm "kinesis-analytics:alarm:health-downtime:2020-04-01" is installed
      | alarmId    | KinesisAnalyticsAppName                                                                    | Threshold | SNSTopicARN                       | EvaluationPeriods | DatapointsToAlarm |
      | under_test | {{cfn-output:KinesisAnalyticsTemplateFlink>KinesisAnalyticsApplicationPhysicalResourceId}} |    0      | {{cfn-output:SnsForAlarms>Topic}} |     1             |     1             |
    And populate input stream with random ticker data for "120" seconds
      | InputStreamName                                                              |
      | {{cfn-output:KinesisAnalyticsTemplateFlink>InputKinesisAnalyticsStreamName}} |
    Then assert metrics for all alarms are populated
