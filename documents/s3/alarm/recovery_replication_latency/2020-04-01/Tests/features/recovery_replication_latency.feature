@s3 @integration @alarm
Feature: Alarm Setup - RecoveryReplicationLatency

  Scenario: Create the alarm based on the RecoveryReplicationLatency metric
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                             | ResourceType | CleanupS3BucketLambdaArn                                    |
      | resource_manager/cloud_formation_templates/shared/CleanupS3BucketLambda.yml | SHARED       |                                                             |
      | resource_manager/cloud_formation_templates/S3Template.yml                   | ON_DEMAND    |{{cfn-output:CleanupS3BucketLambda>CleanupS3BucketLambdaArn}}|
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml          | SHARED       |                                                             |
    And cache bucket replication property "$.ReplicationConfiguration.Rules[0].ID" as "RuleId" "before" SSM automation execution
      | BucketName                                      |
      | {{cfn-output:S3Template>S3BucketToRestoreName}} |
    When alarm "s3:alarm:recovery_replication_latency:2020-04-01" is installed
      | alarmId    | SourceBucketName                                | DestinationBucketName                                | RuleId                  | Threshold | SNSTopicARN                       |
      | under_test | {{cfn-output:S3Template>S3BucketToRestoreName}} | {{cfn-output:S3Template>S3BucketForReplicationName}} | {{cache:before>RuleId}} | 60        | {{cfn-output:SnsForAlarms>Topic}} |
    And put "100" objects into the bucket
      | BucketName                                      |
      | {{cfn-output:S3Template>S3BucketToRestoreName}} |
    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 180 seconds, check every 15 seconds
