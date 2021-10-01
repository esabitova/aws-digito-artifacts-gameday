@kinesis-data-streams @integration @alarm
Feature: Alarm Setup - Kinesis Data Streams WriteProvisionedThroughputExceeded

  Scenario: Create kinesis-data-streams:alarm:write_provisioned_throughput_exceeded:2020-04-01 based on WriteProvisionedThroughputExceeded metric and check OK status
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                    | ResourceType | KmsKey                              |
      | resource_manager/cloud_formation_templates/shared/KMS.yml          | SHARED       |                                     |
      | resource_manager/cloud_formation_templates/KinesisDataStream.yml   | ON_DEMAND    | {{cfn-output:KMS>EncryptAtRestKey}} |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml | SHARED       |                                     |
    When alarm "kinesis-data-streams:alarm:write_provisioned_throughput_exceeded:2020-04-01" is installed
      | alarmId    | KinesisDataStreamName                                  | Threshold | SNSTopicARN                       | EvaluationPeriods | DatapointsToAlarm |
      | under_test | {{cfn-output:KinesisDataStream>KinesisDataStreamName}} | 0         | {{cfn-output:SnsForAlarms>Topic}} | 5                 | 3                 |
    And put "500" records asynchronously in "10" threads with "0" seconds delay between each other to Kinesis Data Stream
      | KinesisDataStreamName                                  |
      | {{cfn-output:KinesisDataStream>KinesisDataStreamName}} |
    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 1200 seconds, check every 15 seconds

  Scenario: Create kinesis-data-streams:alarm:write_provisioned_throughput_exceeded:2020-04-01 based on WriteProvisionedThroughputExceeded metric and check ALARM status
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                    | ResourceType | KmsKey                              |
      | resource_manager/cloud_formation_templates/shared/KMS.yml          | SHARED       |                                     |
      | resource_manager/cloud_formation_templates/KinesisDataStream.yml   | ON_DEMAND    | {{cfn-output:KMS>EncryptAtRestKey}} |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml | SHARED       |                                     |
    When alarm "kinesis-data-streams:alarm:write_provisioned_throughput_exceeded:2020-04-01" is installed
      | alarmId    | KinesisDataStreamName                                  | Threshold | SNSTopicARN                       | EvaluationPeriods | DatapointsToAlarm |
      | under_test | {{cfn-output:KinesisDataStream>KinesisDataStreamName}} | 100       | {{cfn-output:SnsForAlarms>Topic}} | 5                 | 3                 |
    And put "500" records asynchronously in "50" threads with "0" seconds delay between each other to Kinesis Data Stream
      | KinesisDataStreamName                                  |
      | {{cfn-output:KinesisDataStream>KinesisDataStreamName}} |
    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes ALARM within 1200 seconds, check every 15 seconds
