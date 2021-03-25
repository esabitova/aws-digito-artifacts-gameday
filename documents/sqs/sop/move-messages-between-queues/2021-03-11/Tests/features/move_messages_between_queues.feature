@sqs
Feature: SSM automation document to move messages from one queue to another

  Scenario: Move messages from Standard queue to the other Standard queue
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                      | ResourceType |
      | resource_manager/cloud_formation_templates/SqsTemplate.yml                                           | ON_DEMAND    |
      | documents/sqs/sop/move-messages-between-queues/2021-03-11/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And send "40" messages to queue
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And SSM automation document "Digito-MoveMessagesBetweenQueues_2021-03-11" executed
      | SourceQueueUrl                                 | TargetQueueUrl                                            | AutomationAssumeRole                                                                  | MessagesTransferBatchSize | NumberOfMessagesToTransfer | ForceExecution |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} | {{cfn-output:SqsTemplate>SqsDestinationStandardQueueUrl}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoMoveMessagesBetweenQueuesAssumeRole}} | 10                         | 40                         | true           |


    When SSM automation document "Digito-MoveMessagesBetweenQueues_2021-03-11" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

  Scenario: Move messages from Standard queue to the other FIFO queue
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                      | ResourceType |
      | resource_manager/cloud_formation_templates/SqsTemplate.yml                                           | ON_DEMAND    |
      | documents/sqs/sop/move-messages-between-queues/2021-03-11/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
#    And sleep for "60" seconds
#    And purge the queue
#      | QueueUrl                                       |
#      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
#    And purge the queue
#      | QueueUrl                                   |
#      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} |
#    And sleep for "60" seconds
    And send "1" messages to queue
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And SSM automation document "Digito-MoveMessagesBetweenQueues_2021-03-11" executed
      | SourceQueueUrl                                 | TargetQueueUrl                             | AutomationAssumeRole                                                                  | MessagesTransferBatchSize | NumberOfMessagesToTransfer | ForceExecution |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoMoveMessagesBetweenQueuesAssumeRole}} | 1                         | 10                         | true           |


    When SSM automation document "Digito-MoveMessagesBetweenQueues_2021-03-11" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

  Scenario: Move messages from FIFO queue to the other standard queue
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                      | ResourceType |
      | resource_manager/cloud_formation_templates/SqsTemplate.yml                                           | ON_DEMAND    |
      | documents/sqs/sop/move-messages-between-queues/2021-03-11/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
#    And sleep for "60" seconds
#    And purge the queue
#      | QueueUrl                                   |
#      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} |
#    And purge the queue
#      | QueueUrl                                       |
#      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
#    And sleep for "60" seconds
    And send "1" messages to FIFO queue
      | QueueUrl                                   |
      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} |
    And SSM automation document "Digito-MoveMessagesBetweenQueues_2021-03-11" executed
      | SourceQueueUrl                             | TargetQueueUrl                                            | AutomationAssumeRole                                                                  | MessagesTransferBatchSize | NumberOfMessagesToTransfer | ForceExecution |
      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} | {{cfn-output:SqsTemplate>SqsDestinationStandardQueueUrl}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoMoveMessagesBetweenQueuesAssumeRole}} | 1                         | 10                         | true           |


    When SSM automation document "Digito-MoveMessagesBetweenQueues_2021-03-11" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

  Scenario: Move messages from FIFO queue to the other FIFO queue
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                      | ResourceType |
      | resource_manager/cloud_formation_templates/SqsTemplate.yml                                           | ON_DEMAND    |
      | documents/sqs/sop/move-messages-between-queues/2021-03-11/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
#    And sleep for "60" seconds
#    And purge the queue
#      | QueueUrl                                   |
#      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} |
#    And purge the queue
#      | QueueUrl                                             |
#      | {{cfn-output:SqsTemplate>SqsFifoQueueEnabledDlqUrl}} |
#    And sleep for "60" seconds
    And send "1" messages to FIFO queue
      | QueueUrl                                   |
      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} |
    And SSM automation document "Digito-MoveMessagesBetweenQueues_2021-03-11" executed
      | SourceQueueUrl                             | TargetQueueUrl                                       | AutomationAssumeRole                                                                  | MessagesTransferBatchSize | NumberOfMessagesToTransfer | ForceExecution |
      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} | {{cfn-output:SqsTemplate>SqsFifoQueueEnabledDlqUrl}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoMoveMessagesBetweenQueuesAssumeRole}} | 1                         | 10                         | true           |


    When SSM automation document "Digito-MoveMessagesBetweenQueues_2021-03-11" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |