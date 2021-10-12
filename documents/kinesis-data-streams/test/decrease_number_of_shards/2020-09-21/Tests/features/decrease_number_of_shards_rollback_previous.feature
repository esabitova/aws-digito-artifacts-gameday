#@kinesis-data-streams
Feature: SSM automation document Digito-DecreaseNumberOfKinesisDataStreamsShardsTest_2020-09-21

  Scenario: Execute SSM automation document Digito-DecreaseNumberOfKinesisDataStreamsShardsTest_2020-09-21 in rollback
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                                     | ResourceType |
      | resource_manager/cloud_formation_templates/KinesisDataStream.yml                                                    | DEDICATED    |
      | documents/kinesis-data-streams/test/decrease_number_of_shards/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-DecreaseNumberOfKinesisDataStreamsShardsTest_2020-09-21" SSM document
    # Add any pre-execution caching and setup steps here

    When SSM automation document "Digito-DecreaseNumberOfKinesisDataStreamsShardsTest_2020-09-21" executed
    # Add other parameter names below
      | StreamName                                             | AutomationAssumeRole                                                                                 | KinesisDataStreamsUserErrorAlarmName                       |
    # Replace parameter values to point to the corresponding outputs in cloudformation template
      | {{cfn-output:KinesisDataStream>KinesisDataStreamName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoKinesisDataStreamsDecreaseNumberOfShardsAssumeRole}} | {{cfn-output:KinesisDataStream>KinesisDataStreamsAlarmId}} |
    # Add other steps that should parallel to the document here
    And Wait for the SSM automation document "Digito-DecreaseNumberOfKinesisDataStreamsShardsTest_2020-09-21" execution is on step "AssertAlarmToBeRed" in status "InProgress"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And terminate "Digito-DecreaseNumberOfKinesisDataStreamsShardsTest_2020-09-21" SSM automation document
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    Then Wait for the SSM automation document "Digito-DecreaseNumberOfKinesisDataStreamsShardsTest_2020-09-21" execution is on step "TriggerRollback" in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And SSM automation document "Digito-DecreaseNumberOfKinesisDataStreamsShardsTest_2020-09-21" execution in status "Cancelled"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache rollback execution id
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And SSM automation document "Digito-DecreaseNumberOfKinesisDataStreamsShardsTest_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>2}} |
    # Add any post-execution caching and validation here
