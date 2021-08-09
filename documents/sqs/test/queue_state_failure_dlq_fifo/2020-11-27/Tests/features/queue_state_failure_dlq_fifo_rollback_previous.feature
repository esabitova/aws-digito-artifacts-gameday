@sqs
Feature: SSM automation document to test behavior of FIFO queue after receiving a message maximum allowed times

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document to test rollback of a previous execution and move messages from DLQ
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                       | ResourceType |
      | resource_manager/cloud_formation_templates/SqsTemplate.yml                                            | ON_DEMAND    |
      | documents/sqs/test/queue_state_failure_dlq_fifo/2020-11-27/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-QueueStateFailureDlqFifo_2020-11-27" SSM document
    And cache visibility timeout as "VisibilityTimeout" "before" SSM automation execution
      | QueueUrl                                             |
      | {{cfn-output:SqsTemplate>SqsFifoQueueEnabledDlqUrl}} |
    And cache redrive policy as "RedrivePolicy" "before" SSM automation execution
      | QueueUrl                                             |
      | {{cfn-output:SqsTemplate>SqsFifoQueueEnabledDlqUrl}} |
    And purge the queue
      | QueueUrl                                             |
      | {{cfn-output:SqsTemplate>SqsFifoQueueEnabledDlqUrl}} |
    # only one PurgeQueue is allowed during 60 seconds
    And sleep for "60" seconds
    And purge the queue
      | QueueUrl                                         |
      | {{cfn-output:SqsTemplate>SqsDlqForFifoQueueUrl}} |
    And cache number of messages in queue as "NumberOfMessagesDLQ" "before" SSM automation execution
      | QueueUrl                                         |
      | {{cfn-output:SqsTemplate>SqsDlqForFifoQueueUrl}} |
    And SSM automation document "Digito-QueueStateFailureDlqFifo_2020-11-27" executed
      | QueueUrl                                             | AutomationAssumeRole                                                                 | DeadLetterQueueAlarmName                            | MoveMessagesFromDeadLetterQueue |
      | {{cfn-output:SqsTemplate>SqsFifoQueueEnabledDlqUrl}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoQueueStateFailureDlqFifoAssumeRole}} | {{cfn-output:SqsTemplate>DlqMessageFifoQueueAlarm}} | True                            |
    And send "100" messages to FIFO queue
      | QueueUrl                                             |
      | {{cfn-output:SqsTemplate>SqsFifoQueueEnabledDlqUrl}} |

    When Wait for the SSM automation document "Digito-QueueStateFailureDlqFifo_2020-11-27" execution is on step "AssertAlarmToBeRed" in status "InProgress"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    Then terminate "Digito-QueueStateFailureDlqFifo_2020-11-27" SSM automation document
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    Then Wait for the SSM automation document "Digito-QueueStateFailureDlqFifo_2020-11-27" execution is on step "TriggerRollback" in status "Success"
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|
    And SSM automation document "Digito-QueueStateFailureDlqFifo_2020-11-27" execution in status "Cancelled"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    Then cache rollback execution id
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|

    When SSM automation document "Digito-QueueStateFailureDlqFifo_2020-11-27" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>2}} |
    And sleep for "60" seconds
    And cache visibility timeout as "VisibilityTimeout" "after" SSM automation execution
      | QueueUrl                                             |
      | {{cfn-output:SqsTemplate>SqsFifoQueueEnabledDlqUrl}} |
    And cache redrive policy as "RedrivePolicy" "after" SSM automation execution
      | QueueUrl                                             |
      | {{cfn-output:SqsTemplate>SqsFifoQueueEnabledDlqUrl}} |
    And cache number of messages in queue as "NumberOfMessagesDLQ" "after" SSM automation execution
      | QueueUrl                                         |
      | {{cfn-output:SqsTemplate>SqsDlqForFifoQueueUrl}} |
    And cache number of messages in queue as "NumberOfMessages" "after" SSM automation execution
      | QueueUrl                                         |
      | {{cfn-output:SqsTemplate>SqsFifoQueueEnabledDlqUrl}} |
    And purge the queue
      | QueueUrl                                             |
      | {{cfn-output:SqsTemplate>SqsFifoQueueEnabledDlqUrl}} |
    # only one PurgeQueue is allowed during 60 seconds
    And sleep for "60" seconds
    And purge the queue
      | QueueUrl                                         |
      | {{cfn-output:SqsTemplate>SqsDlqForFifoQueueUrl}} |

    Then assert "VisibilityTimeout" at "before" became equal to "VisibilityTimeout" at "after"
    And assert "RedrivePolicy" at "before" became equal to "RedrivePolicy" at "after"
    And assert "NumberOfMessagesDLQ" at "before" became equal to "NumberOfMessagesDLQ" at "after"
    And assert "NumberOfMessages" at "after" became equal to "100"