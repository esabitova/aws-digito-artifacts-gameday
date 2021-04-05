@sqs
Feature: SSM automation document to test behavior of FIFO queue after receiving a message maximum allowed times

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document to test behavior of FIFO queue after receiving a message maximum allowed times and purge DLQ afterwards
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                       | ResourceType |
      | resource_manager/cloud_formation_templates/SqsTemplate.yml                                            | ON_DEMAND    |
      | documents/sqs/test/queue_state_failure_dlq_fifo/2020-11-27/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-QueueStateFailureDlqFifo_2020-11-27" SSM document
    And cache policy as "Policy" "before" SSM automation execution
      | QueueUrl                                             |
      | {{cfn-output:SqsTemplate>SqsFifoQueueEnabledDlqUrl}} |
    And cache visibility timeout as "VisibilityTimeout" "before" SSM automation execution
      | QueueUrl                                                 |
      | {{cfn-output:SqsTemplate>SqsFifoQueueEnabledDlqUrl}} |
    And cache redrive policy as "RedrivePolicy" "before" SSM automation execution
      | QueueUrl                                                 |
      | {{cfn-output:SqsTemplate>SqsFifoQueueEnabledDlqUrl}} |
    And purge the queue
      | QueueUrl                                         |
      | {{cfn-output:SqsTemplate>SqsDlqForFifoQueueUrl}} |
    And sleep for "60" seconds
    And cache number of messages in queue as "NumberOfMessages" "before" SSM automation execution
      | QueueUrl                                         |
      | {{cfn-output:SqsTemplate>SqsDlqForFifoQueueUrl}} |
    And SSM automation document "Digito-QueueStateFailureDlqFifo_2020-11-27" executed
      | QueueUrl                                             | AutomationAssumeRole                                                                 | DeadLetterQueueAlarmName                            | PurgeDeadLetterQueue |
      | {{cfn-output:SqsTemplate>SqsFifoQueueEnabledDlqUrl}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoQueueStateFailureDlqFifoAssumeRole}} | {{cfn-output:SqsTemplate>DlqMessageFifoQueueAlarm}} | True                 |

    When SSM automation document "Digito-QueueStateFailureDlqFifo_2020-11-27" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache policy as "Policy" "after" SSM automation execution
      | QueueUrl                                             |
      | {{cfn-output:SqsTemplate>SqsFifoQueueEnabledDlqUrl}} |
    And cache visibility timeout as "VisibilityTimeout" "after" SSM automation execution
      | QueueUrl                                                 |
      | {{cfn-output:SqsTemplate>SqsFifoQueueEnabledDlqUrl}} |
    And cache redrive policy as "RedrivePolicy" "after" SSM automation execution
      | QueueUrl                                                 |
      | {{cfn-output:SqsTemplate>SqsFifoQueueEnabledDlqUrl}} |
    And cache number of messages in queue as "NumberOfMessages" "after" SSM automation execution
      | QueueUrl                                         |
      | {{cfn-output:SqsTemplate>SqsDlqForFifoQueueUrl}} |


    Then assert "Policy" at "before" became equal to "Policy" at "after"
    Then assert "VisibilityTimeout" at "before" became equal to "VisibilityTimeout" at "after"
    Then assert "RedrivePolicy" at "before" became equal to "RedrivePolicy" at "after"
    And assert "NumberOfMessages" at "before" became equal to "NumberOfMessages" at "after"