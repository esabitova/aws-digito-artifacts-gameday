#@kinesis-data-streams
Feature: SSM automation document Digito-DecreaseNumberOfShards_2020-09-21

  Scenario: Execute SSM automation document Digito-DecreaseNumberOfShards_2020-09-21 to test failure case
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                                     | ResourceType |
      | resource_manager/cloud_formation_templates/KinesisDataStream.yml                                                    | DEDICATED    |
      | documents/kinesis-data-streams/test/decrease_number_of_shards/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-DecreaseNumberOfShards_2020-09-21" SSM document
    And cache by "describe_stream_summary" method of "kinesis" to "before"
      | Input-StreamName                                       | Output-OldShardCount                      |
      | {{cfn-output:KinesisDataStream>KinesisDataStreamName}} | $.StreamDescriptionSummary.OpenShardCount |

    When SSM automation document "Digito-DecreaseNumberOfShards_2020-09-21" executed
    # Add other parameter names below
      | StreamName                                             | AutomationAssumeRole                                                                                 | KinesisDataStreamsUserErrorAlarmName           |
    # Replace parameter values to point to the corresponding outputs in cloudformation template
      | {{cfn-output:KinesisDataStream>KinesisDataStreamName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoKinesisDataStreamsDecreaseNumberOfShardsAssumeRole}} | {{cfn-output:KinesisDataStream>AlwaysOKAlarm}} |
    # Add other steps that should parallel to the document here
    And Wait for the SSM automation document "Digito-DecreaseNumberOfShards_2020-09-21" execution is on step "AssertAlarmToBeRed" in status "TimedOut"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    # Add any step required to rectify the alarm here

    Then Wait for the SSM automation document "Digito-DecreaseNumberOfShards_2020-09-21" execution is on step "AssertAlarmToBeGreen" in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And SSM automation document "Digito-DecreaseNumberOfShards_2020-09-21" execution in status "TimedOut"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And assert "RecordStartTime, AssertStreamInActiveState, UpdateKinesisDataStreamsShardCount, WaitStreamForAnActiveState, GetActualShardCount, CheckIfTargetCountEqualsToActualShardCount, OutputRecoveryTime" steps are successfully executed in order
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache by "describe_stream_summary" method of "kinesis" to "after"
      | Input-StreamName                                       | Output-ActualShardCount                   |
      | {{cfn-output:KinesisDataStream>KinesisDataStreamName}} | $.StreamDescriptionSummary.OpenShardCount |
    And assert "OldShardCount" at "before" became equal to "ActualShardCount" at "after"

