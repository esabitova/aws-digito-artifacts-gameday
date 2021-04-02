@sqs
Feature: SSM automation document to block sqs:DeleteMessage

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document to block sqs:DeleteMessage
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                               | ResourceType |
      | resource_manager/cloud_formation_templates/SqsTemplate.yml                                    | ON_DEMAND    |
      | documents/sqs/test/block_delete_message/2021-03-09/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-BlockSQSDeleteMessage_2021-03-09" SSM document
    And cache policy as "Policy" "before" SSM automation execution
      | QueueUrl                                   |
      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} |
    And purge the queue
      | QueueUrl                                   |
      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} |
    # Only one PurgeQueue operation is allowed every 60 seconds.
    And sleep for "60" seconds
    And cache number of messages in queue as "NumberOfMessages" "before" SSM automation execution
      | QueueUrl                                   |
      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} |
    And SSM automation document "Digito-BlockSQSDeleteMessage_2021-03-09" executed
      | QueueUrl                                   | AutomationAssumeRole                                                              | SQSUserErrorAlarmName                                                    |
      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoBlockSQSDeleteMessageAssumeRole}} | {{cfn-output:SqsTemplate>ApproximateAgeOfOldestMessageMaximumFifoAlarm}} |

    When send "5" messages to FIFO queue
      | QueueUrl                                   |
      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} |
    And sleep for "10" seconds
    And purge the queue
      | QueueUrl                                   |
      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} |
    And Wait for the SSM automation document "Digito-BlockSQSDeleteMessage_2021-03-09" execution is on step "AssertAlarmToBeGreenBeforeTest" in status "Success" for "1000" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And Wait for the SSM automation document "Digito-BlockSQSDeleteMessage_2021-03-09" execution is on step "UpdatePolicy" in status "Success" for "1000" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And sleep for "60" seconds
    And send "5" messages to FIFO queue
      | QueueUrl                                   |
      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} |
    And Wait for the SSM automation document "Digito-BlockSQSDeleteMessage_2021-03-09" execution is on step "AssertAlarmToBeRed" in status "Success" for "600" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache number of messages in queue as "NumberOfMessages" "after-send" SSM automation execution
      | QueueUrl                                   |
      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} |
    And Wait for the SSM automation document "Digito-BlockSQSDeleteMessage_2021-03-09" execution is on step "RollbackCurrentExecution" in status "Success" for "1000" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And purge the queue
      | QueueUrl                                   |
      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} |
    And sleep for "60" seconds
    And send "5" messages to FIFO queue
      | QueueUrl                                   |
      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} |
    And sleep for "5" seconds
    And purge the queue
      | QueueUrl                                   |
      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} |
    And sleep for "60" seconds
    And SSM automation document "Digito-BlockSQSDeleteMessage_2021-03-09" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache number of messages in queue as "NumberOfMessages" "after" SSM automation execution
      | QueueUrl                                   |
      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} |
    And cache policy as "Policy" "after" SSM automation execution
      | QueueUrl                                   |
      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} |

    Then assert "NumberOfMessages" at "before" became equal to "NumberOfMessages" at "after"
    And assert "NumberOfMessages" at "after-send" became not equal to "NumberOfMessages" at "before"
    And assert "NumberOfMessages" at "after" became equal to "0"
    And assert "Policy" at "before" became equal to "Policy" at "after"
