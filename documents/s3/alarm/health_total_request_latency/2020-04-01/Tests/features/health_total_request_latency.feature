@s3 @integration @alarm
Feature: Alarm Setup - TotalRequestLatency

  Scenario: Create the alarm based on the TotalRequestLatency metric
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                    | ResourceType |
      | resource_manager/cloud_formation_templates/S3Template.yml          | ON_DEMAND    |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml | SHARED       |
    When alarm "s3:alarm:health_total_request_latency:2020-04-01" is installed
      | alarmId    | S3BucketName                                    | Threshold | SNSTopicARN                       |
      | under_test | {{cfn-output:S3Template>S3BucketToRestoreName}} | 2000      | {{cfn-output:SnsForAlarms>Topic}} |
    And put "1" objects into the bucket
      | BucketName                                      |
      | {{cfn-output:S3Template>S3BucketToRestoreName}} |
    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 180 seconds, check every 15 seconds