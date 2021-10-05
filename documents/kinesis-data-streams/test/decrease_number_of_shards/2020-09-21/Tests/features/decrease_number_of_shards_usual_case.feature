@kinesis-data-streams
Feature: SSM automation document Digito-DecreaseNumberOfShards_2020-09-21

  Scenario: Execute Digito-DecreaseNumberOfShards_2020-09-21 in usual case
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                                     | ResourceType | KmsKey                              |
      | resource_manager/cloud_formation_templates/shared/KMS.yml                                                           | SHARED       |                                     |
      | resource_manager/cloud_formation_templates/KinesisDataStream.yml                                                    | DEDICATED    | {{cfn-output:KMS>EncryptAtRestKey}} |
      | documents/kinesis-data-streams/test/decrease_number_of_shards/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                                     |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml                                                  | SHARED       |                                     |
    And published "Digito-DecreaseNumberOfShards_2020-09-21" SSM document
    And cache values to "before"
      | StreamName                                             |
      | {{cfn-output:KinesisDataStream>KinesisDataStreamName}} |
    And alarm "kinesis-data-streams:alarm:write_provisioned_throughput_exceeded:2020-04-01" is installed
      | alarmId    | KinesisDataStreamName                                  | Threshold | SNSTopicARN                       | EvaluationPeriods | DatapointsToAlarm |
      | under_test | {{cfn-output:KinesisDataStream>KinesisDataStreamName}} | 0         | {{cfn-output:SnsForAlarms>Topic}} | 5                 | 3                 |
    And cache by "describe_stream_summary" method of "kinesis" to "before"
      | Input-StreamName                                       | Output-OldShardCount                      |
      | {{cfn-output:KinesisDataStream>KinesisDataStreamName}} | $.StreamDescriptionSummary.OpenShardCount |
    And calculate "{{cache:before>OldShardCount}}" "*" "2" and cache result as "ExpectedShardCount" "before" SSM automation execution
    And SSM automation document "Digito-DecreaseNumberOfShards_2020-09-21" executed
      | StreamName                                             | AutomationAssumeRole                                                                                 | TargetShardCount                    |
      | {{cfn-output:KinesisDataStream>KinesisDataStreamName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoKinesisDataStreamsDecreaseNumberOfShardsAssumeRole}} | {{cache:before>ExpectedShardCount}} |
    And SSM automation document "Digito-DecreaseNumberOfShards_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache by "describe_stream_summary" method of "kinesis" to "after_increasing"
      | Input-StreamName                                       | Output-ActualShardCount                   |
      | {{cfn-output:KinesisDataStream>KinesisDataStreamName}} | $.StreamDescriptionSummary.OpenShardCount |
    And assert "ExpectedShardCount" at "before" became equal to "ActualShardCount" at "after_increasing"

    When SSM automation document "Digito-DecreaseNumberOfShards_2020-09-21" executed
      | StreamName                                             | AutomationAssumeRole                                                                                 | KinesisDataStreamsUserErrorAlarmName |
      | {{cfn-output:KinesisDataStream>KinesisDataStreamName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoKinesisDataStreamsDecreaseNumberOfShardsAssumeRole}} | {{alarm:under_test>AlarmName}}       |

    Then SSM automation document "Digito-DecreaseNumberOfShards_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>2}} |
    And assert "CheckIsRollback, AssertAlarmToBeGreenBeforeTest, BackupCurrentExecution, DecreaseShardCountToOneShard, AssertAlarmToBeRed, RollbackCurrentExecution, AssertAlarmToBeGreen, TriggerRollback" steps are successfully executed in order
      | ExecutionId                |
      | {{cache:SsmExecutionId>2}} |
    And cache by "describe_stream_summary" method of "kinesis" to "after"
      | Input-StreamName                                       | Output-ActualShardCount                   |
      | {{cfn-output:KinesisDataStream>KinesisDataStreamName}} | $.StreamDescriptionSummary.OpenShardCount |
    And assert "ActualShardCount" at "after_increasing" became equal to "ActualShardCount" at "after"

