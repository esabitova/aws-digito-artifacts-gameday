@kinesis-analytics @integration @alarm
Feature: Alarm Setup - Kinesis Analytics Errors
  Scenario: Create kinesis:alarm:data_analytics_lambda_delivery_duration:2020-04-01 based on LambdaDelivery.DeliveryFailedRecords metric and check OK status
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                              | ResourceType | KmsKey                              |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml           | SHARED       |                                     |
      | resource_manager/cloud_formation_templates/shared/KMS.yml                    | SHARED       |                                     |
      | resource_manager/cloud_formation_templates/KinesisAnalyticsTemplateSQL.yml   | ON_DEMAND    | {{cfn-output:KMS>EncryptAtRestKey}} |
    And cache Kinesis Data Analytics for "SQL" application InputId as KinesisAnalyticsInputId and OutputId as KinesisAnalyticsOutputId "before" SSM automation execution
      | KinesisAnalyticsApplicationName                                                          |
      | {{cfn-output:KinesisAnalyticsTemplateSQL>KinesisAnalyticsApplicationPhysicalResourceId}} |
    And start Kinesis Data Analytics for "SQL" application
      | KinesisAnalyticsInputId                  | KinesisAnalyticsAppName                                                                  |
      | {{cache:before>KinesisAnalyticsInputId}} | {{cfn-output:KinesisAnalyticsTemplateSQL>KinesisAnalyticsApplicationPhysicalResourceId}} |
    When alarm "kinesis-analytics:alarm:recovery-lambda_delivery_duration:2020-04-01" is installed
      | alarmId    | KinesisAnalyticsOutputId                  | KinesisAnalyticsAppName                                                                  | Threshold | SNSTopicARN                       | EvaluationPeriods | DatapointsToAlarm |
      | under_test | {{cache:before>KinesisAnalyticsOutputId}} | {{cfn-output:KinesisAnalyticsTemplateSQL>KinesisAnalyticsApplicationPhysicalResourceId}} |    5      | {{cfn-output:SnsForAlarms>Topic}} |     1             |     1             |
    And populate input stream with random ml data for "60" seconds
      | InputStreamName                                                            |
      | {{cfn-output:KinesisAnalyticsTemplateSQL>InputKinesisAnalyticsStreamName}} |
   Then assert metrics for all alarms are populated
