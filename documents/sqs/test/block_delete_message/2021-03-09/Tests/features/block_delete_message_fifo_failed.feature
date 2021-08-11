@sqs
Feature: SSM automation document to block sqs:DeleteMessage

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document to block sqs:DeleteMessage
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                               | ResourceType |
      | resource_manager/cloud_formation_templates/SqsTemplate.yml                                    | ON_DEMAND    |
      | documents/sqs/test/block_delete_message/2021-03-09/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml                            | SHARED       |
    And alarm "sqs:alarm:health_alarm_approximate_age_of_oldest_message_maximum:2020-11-26" is installed
      | alarmId    | SNSTopicARN                       | QueueName                                   | Threshold
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:SqsTemplate>SqsFifoQueueName}} | 15
    And published "Digito-BlockSQSDeleteMessage_2021-03-09" SSM document
    And cache policy as "Policy" "before" SSM automation execution
      | QueueUrl                                   |
      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} |
    # only one PurgeQueue is allowed during 60 seconds
    And sleep for "60" seconds
    And purge the queue
      | QueueUrl                                   |
      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} |
    And cache number of messages in queue as "NumberOfMessages" "before" SSM automation execution
      | QueueUrl                                   |
      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} |
    And SSM automation document "Digito-BlockSQSDeleteMessage_2021-03-09" executed
      | QueueUrl                                   | AutomationAssumeRole                                                              | SQSUserErrorAlarmName          |
      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoBlockSQSDeleteMessageAssumeRole}} | {{alarm:under_test>AlarmName}} |

    # Don't send messages to keep alarm OK and fail
    When Wait for the SSM automation document "Digito-BlockSQSDeleteMessage_2021-03-09" execution is on step "AssertAlarmToBeRed" in status "TimedOut"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And SSM automation document "Digito-BlockSQSDeleteMessage_2021-03-09" execution in status "TimedOut"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache number of messages in queue as "NumberOfMessages" "after" SSM automation execution
      | QueueUrl                                   |
      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} |
    And cache policy as "Policy" "after" SSM automation execution
      | QueueUrl                                   |
      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} |

    Then assert "NumberOfMessages" at "before" became equal to "NumberOfMessages" at "after"
    And assert "NumberOfMessages" at "after" became equal to "0"
    And assert "Policy" at "before" became equal to "Policy" at "after"
    And assert "CheckIsRollback, AssertAlarmToBeGreenBeforeTest, BackupCurrentExecution, GetPolicyWithDenyOnDeleteMessageAction, UpdatePolicy, RollbackCurrentExecution, AssertAlarmToBeGreen" steps are successfully executed in order
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
