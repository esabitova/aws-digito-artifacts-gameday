@sqs
Feature: SSM automation document to move messages from one queue to another


  Scenario: Move messages from Standard queue to the other FIFO queue with ForceExecution = false
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                      | ResourceType |
      | resource_manager/cloud_formation_templates/SqsTemplate.yml                                           | ON_DEMAND    |
      | documents/sqs/sop/move-messages-between-queues/2021-03-11/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-MoveMessagesBetweenQueues_2021-03-11" SSM document
    And send "10" messages to queue
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And SSM automation document "Digito-MoveMessagesBetweenQueues_2021-03-11" executed
      | SourceQueueUrl                                 | TargetQueueUrl                             | AutomationAssumeRole                                                                  | MessagesTransferBatchSize | NumberOfMessagesToTransfer | ForceExecution |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoMoveMessagesBetweenQueuesAssumeRole}} | 10                        | 40                         | false           |


    When SSM automation document "Digito-MoveMessagesBetweenQueues_2021-03-11" execution in status "Failed"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

  Scenario: Move messages from FIFO queue to the other standard queue with ForceExecution = false
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                      | ResourceType |
      | resource_manager/cloud_formation_templates/SqsTemplate.yml                                           | ON_DEMAND    |
      | documents/sqs/sop/move-messages-between-queues/2021-03-11/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-MoveMessagesBetweenQueues_2021-03-11" SSM document
    And send "10" messages to FIFO queue
      | QueueUrl                                   |
      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} |
    And SSM automation document "Digito-MoveMessagesBetweenQueues_2021-03-11" executed
      | SourceQueueUrl                             | TargetQueueUrl                                            | AutomationAssumeRole                                                                  | MessagesTransferBatchSize | NumberOfMessagesToTransfer | ForceExecution |
      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} | {{cfn-output:SqsTemplate>SqsDestinationStandardQueueUrl}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoMoveMessagesBetweenQueuesAssumeRole}} | 10                        | 40                         | false           |


    When SSM automation document "Digito-MoveMessagesBetweenQueues_2021-03-11" execution in status "Failed"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

