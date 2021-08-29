@kinesis-data-streams
Feature: SSM automation document Digito-UpdateShardCount_2020-10-26

  Scenario: Execute Digito-UpdateShardCount_2020-10-26 two times to increase the number of shards and decrease back
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                             | ResourceType | KmsKey                              |
      | resource_manager/cloud_formation_templates/shared/KMS.yml                                                   | SHARED       |                                     |
      | resource_manager/cloud_formation_templates/KinesisDataStream.yml                                            | ON_DEMAND    | {{cfn-output:KMS>EncryptAtRestKey}} |
      | documents/kinesis-data-streams/sop/update_shard_count/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                                     |
    And published "Digito-UpdateShardCount_2020-10-26" SSM document
    # Firstly, increase the number of shards in the stream
    And cache by "describe-stream-summary" method of "kinesis" to "before_increasing"
      | Input-StreamName                                       | Output-OldShardCount                      |
      | {{cfn-output:KinesisDataStream>KinesisDataStreamName}} | $.StreamDescriptionSummary.OpenShardCount |
    And calculate "{{cache:before_increasing>OldShardCount}}" "+" "1" and cache result as "ExpectedShardCount" "before_increasing" SSM automation execution

    When SSM automation document "Digito-UpdateShardCount_2020-10-26" executed
      | StreamName                                             | AutomationAssumeRole                                                                           | TargetShardCount                               |
      | {{cfn-output:KinesisDataStream>KinesisDataStreamName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoKinesisDataStreamsUpdateShardCountAssumeRole}} | {{cache:before_increasing>ExpectedShardCount}} |

    Then SSM automation document "Digito-UpdateShardCount_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And assert "RecordStartTime, AssertStreamInActiveState, UpdateShardCount, WaitStreamForAnActiveState, GetShardCount, OutputRecoveryTime" steps are successfully executed in order
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache by "describe-stream-summary" method of "kinesis" to "after_increasing"
      | Input-StreamName                                       | Output-ActualShardCount                   |
      | {{cfn-output:KinesisDataStream>KinesisDataStreamName}} | $.StreamDescriptionSummary.OpenShardCount |
    And assert "OldShardCount" at "before_increasing" became not equal to "ActualShardCount" at "after_increasing"
    And assert "ExpectedShardCount" at "before_increasing" became equal to "ActualShardCount" at "after_increasing"
    
    # Secondly, decrease back the number of shards in the stream
    And calculate "{{cache:after_increasing>ActualShardCount}}" "-" "1" and cache result as "ExpectedShardCount" "before_decreasing" SSM automation execution

    When SSM automation document "Digito-UpdateShardCount_2020-10-26" executed
      | StreamName                                             | AutomationAssumeRole                                                                           | TargetShardCount                               |
      | {{cfn-output:KinesisDataStream>KinesisDataStreamName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoKinesisDataStreamsUpdateShardCountAssumeRole}} | {{cache:before_decreasing>ExpectedShardCount}} |

    Then SSM automation document "Digito-UpdateShardCount_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>2}} |
    And assert "RecordStartTime, AssertStreamInActiveState, UpdateShardCount, WaitStreamForAnActiveState, GetShardCount, OutputRecoveryTime" steps are successfully executed in order
      | ExecutionId                |
      | {{cache:SsmExecutionId>2}} |
    And cache by "describe-stream-summary" method of "kinesis" to "after_decreasing"
      | Input-StreamName                                       | Output-ActualShardCount                   |
      | {{cfn-output:KinesisDataStream>KinesisDataStreamName}} | $.StreamDescriptionSummary.OpenShardCount |
    And assert "ActualShardCount" at "after_increasing" became not equal to "ActualShardCount" at "after_decreasing"
    And assert "ExpectedShardCount" at "before_decreasing" became equal to "ActualShardCount" at "after_decreasing"


  Scenario: Execute Digito-UpdateShardCount_2020-10-26 to pass the same number of shards as it was before
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                             | ResourceType | KmsKey                              |
      | resource_manager/cloud_formation_templates/shared/KMS.yml                                                   | SHARED       |                                     |
      | resource_manager/cloud_formation_templates/KinesisDataStream.yml                                            | ON_DEMAND    | {{cfn-output:KMS>EncryptAtRestKey}} |
      | documents/kinesis-data-streams/sop/update_shard_count/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                                     |
    And published "Digito-UpdateShardCount_2020-10-26" SSM document
    And cache by "describe-stream-summary" method of "kinesis" to "before"
      | Input-StreamName                                       | Output-OldShardCount                      |
      | {{cfn-output:KinesisDataStream>KinesisDataStreamName}} | $.StreamDescriptionSummary.OpenShardCount |

    When SSM automation document "Digito-UpdateShardCount_2020-10-26" executed
      | StreamName                                             | AutomationAssumeRole                                                                           | TargetShardCount                               |
      | {{cfn-output:KinesisDataStream>KinesisDataStreamName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoKinesisDataStreamsUpdateShardCountAssumeRole}} | {{cache:before>OldShardCount}} |

    Then SSM automation document "Digito-UpdateShardCount_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And assert "RecordStartTime, AssertStreamInActiveState, UpdateShardCount, WaitStreamForAnActiveState, GetShardCount, OutputRecoveryTime" steps are successfully executed in order
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache by "describe-stream-summary" method of "kinesis" to "after"
      | Input-StreamName                                       | Output-ActualShardCount                   |
      | {{cfn-output:KinesisDataStream>KinesisDataStreamName}} | $.StreamDescriptionSummary.OpenShardCount |
    And assert "OldShardCount" at "before" became equal to "ActualShardCount" at "after"
