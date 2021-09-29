@sqs
Feature: SSM automation document to move messages from one queue to another

  Scenario: Move messages from Standard queue to the other Standard queue
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                      | ResourceType |
      | resource_manager/cloud_formation_templates/SqsTemplate.yml                                           | ON_DEMAND    |
      | documents/sqs/sop/move-messages-between-queues/2021-03-11/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-MoveSQSMessagesBetweenQueuesSOP_2021-03-11" SSM document
    And cache number of messages in queue as "TargetNumberOfMessages" "before" SSM automation execution
      | QueueUrl                                             |
      | {{cfn-output:SqsTemplate>SqsDlqForStandardQueueUrl}} |
    And send "100" messages to queue
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And sleep for "60" seconds
    And cache number of messages in queue as "SourceNumberOfMessages" "before" SSM automation execution
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And SSM automation document "Digito-MoveSQSMessagesBetweenQueuesSOP_2021-03-11" executed
      | SourceQueueUrl                                 | TargetQueueUrl                                       | AutomationAssumeRole                                                                        | MessagesTransferBatchSize | NumberOfMessagesToTransfer | ForceExecution |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} | {{cfn-output:SqsTemplate>SqsDlqForStandardQueueUrl}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoMoveSQSMessagesBetweenQueuesSOPAssumeRole}} | 5                         | 10                         | false          |

    When SSM automation document "Digito-MoveSQSMessagesBetweenQueuesSOP_2021-03-11" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And sleep for "60" seconds
    And cache number of messages in queue as "SourceNumberOfMessages" "after" SSM automation execution
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And cache number of messages in queue as "TargetNumberOfMessages" "after" SSM automation execution
      | QueueUrl                                             |
      | {{cfn-output:SqsTemplate>SqsDlqForStandardQueueUrl}} |
    And purge the queue
      | QueueUrl                                             |
      | {{cfn-output:SqsTemplate>SqsDlqForStandardQueueUrl}} |

    Then assert the difference between "SourceNumberOfMessages" at "before" and "SourceNumberOfMessages" at "after" became "10"
    And assert the difference between "TargetNumberOfMessages" at "after" and "TargetNumberOfMessages" at "before" became "10"


  Scenario: Move messages from Standard queue to the other FIFO queue
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                      | ResourceType |
      | resource_manager/cloud_formation_templates/SqsTemplate.yml                                           | ON_DEMAND    |
      | documents/sqs/sop/move-messages-between-queues/2021-03-11/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-MoveSQSMessagesBetweenQueuesSOP_2021-03-11" SSM document
    And cache number of messages in queue as "SourceNumberOfMessages" "before" SSM automation execution
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And cache number of messages in queue as "TargetNumberOfMessages" "before" SSM automation execution
      | QueueUrl                                   |
      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} |
    And send "10" messages to queue
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And SSM automation document "Digito-MoveSQSMessagesBetweenQueuesSOP_2021-03-11" executed
      | SourceQueueUrl                                 | TargetQueueUrl                             | AutomationAssumeRole                                                                        | MessagesTransferBatchSize | NumberOfMessagesToTransfer | ForceExecution |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoMoveSQSMessagesBetweenQueuesSOPAssumeRole}} | 5                         | 10                         | true           |

    When SSM automation document "Digito-MoveSQSMessagesBetweenQueuesSOP_2021-03-11" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And sleep for "60" seconds
    And cache number of messages in queue as "SourceNumberOfMessages" "after" SSM automation execution
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And cache number of messages in queue as "TargetNumberOfMessages" "after" SSM automation execution
      | QueueUrl                                   |
      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} |
    And purge the queue
      | QueueUrl                                   |
      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} |

    Then assert "SourceNumberOfMessages" at "before" became equal to "SourceNumberOfMessages" at "after"
    And assert the difference between "TargetNumberOfMessages" at "after" and "TargetNumberOfMessages" at "before" became "10"


  Scenario: Move messages from FIFO queue to the other standard queue
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                      | ResourceType |
      | resource_manager/cloud_formation_templates/SqsTemplate.yml                                           | ON_DEMAND    |
      | documents/sqs/sop/move-messages-between-queues/2021-03-11/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-MoveSQSMessagesBetweenQueuesSOP_2021-03-11" SSM document
    And cache number of messages in queue as "SourceNumberOfMessages" "before" SSM automation execution
      | QueueUrl                                   |
      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} |
    And cache number of messages in queue as "TargetNumberOfMessages" "before" SSM automation execution
      | QueueUrl                                             |
      | {{cfn-output:SqsTemplate>SqsDlqForStandardQueueUrl}} |
    And send "10" messages to FIFO queue
      | QueueUrl                                   |
      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} |
    And SSM automation document "Digito-MoveSQSMessagesBetweenQueuesSOP_2021-03-11" executed
      | SourceQueueUrl                             | TargetQueueUrl                                       | AutomationAssumeRole                                                                        | MessagesTransferBatchSize | NumberOfMessagesToTransfer | ForceExecution |
      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} | {{cfn-output:SqsTemplate>SqsDlqForStandardQueueUrl}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoMoveSQSMessagesBetweenQueuesSOPAssumeRole}} | 5                         | 10                         | true           |

    When SSM automation document "Digito-MoveSQSMessagesBetweenQueuesSOP_2021-03-11" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And sleep for "60" seconds
    And cache number of messages in queue as "SourceNumberOfMessages" "after" SSM automation execution
      | QueueUrl                                   |
      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} |
    And cache number of messages in queue as "TargetNumberOfMessages" "after" SSM automation execution
      | QueueUrl                                             |
      | {{cfn-output:SqsTemplate>SqsDlqForStandardQueueUrl}} |
    And purge the queue
      | QueueUrl                                             |
      | {{cfn-output:SqsTemplate>SqsDlqForStandardQueueUrl}} |

    Then assert "SourceNumberOfMessages" at "before" became equal to "SourceNumberOfMessages" at "after"
    And assert the difference between "TargetNumberOfMessages" at "after" and "TargetNumberOfMessages" at "before" became "10"


  Scenario: Move messages from FIFO queue to the other FIFO queue
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                      | ResourceType |
      | resource_manager/cloud_formation_templates/SqsTemplate.yml                                           | ON_DEMAND    |
      | documents/sqs/sop/move-messages-between-queues/2021-03-11/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-MoveSQSMessagesBetweenQueuesSOP_2021-03-11" SSM document
    And cache number of messages in queue as "SourceNumberOfMessages" "before" SSM automation execution
      | QueueUrl                                   |
      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} |
    And cache number of messages in queue as "TargetNumberOfMessages" "before" SSM automation execution
      | QueueUrl                                             |
      | {{cfn-output:SqsTemplate>SqsFifoQueueEnabledDlqUrl}} |
    And send "10" messages to FIFO queue
      | QueueUrl                                   |
      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} |
    And SSM automation document "Digito-MoveSQSMessagesBetweenQueuesSOP_2021-03-11" executed
      | SourceQueueUrl                             | TargetQueueUrl                                       | AutomationAssumeRole                                                                        | MessagesTransferBatchSize | NumberOfMessagesToTransfer | ForceExecution |
      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} | {{cfn-output:SqsTemplate>SqsFifoQueueEnabledDlqUrl}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoMoveSQSMessagesBetweenQueuesSOPAssumeRole}} | 5                         | 10                         | false          |


    When SSM automation document "Digito-MoveSQSMessagesBetweenQueuesSOP_2021-03-11" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache number of messages in queue as "SourceNumberOfMessages" "after" SSM automation execution
      | QueueUrl                                   |
      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} |
    And cache number of messages in queue as "TargetNumberOfMessages" "after" SSM automation execution
      | QueueUrl                                             |
      | {{cfn-output:SqsTemplate>SqsFifoQueueEnabledDlqUrl}} |
    And purge the queue
      | QueueUrl                                             |
      | {{cfn-output:SqsTemplate>SqsFifoQueueEnabledDlqUrl}} |

    Then assert "SourceNumberOfMessages" at "before" became equal to "SourceNumberOfMessages" at "after"
    And assert the difference between "TargetNumberOfMessages" at "after" and "TargetNumberOfMessages" at "before" became "10"


  Scenario: Move messages from Standard queue to the other Standard queue with a lot of messages
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                      | ResourceType |
      | resource_manager/cloud_formation_templates/SqsTemplate.yml                                           | ON_DEMAND    |
      | documents/sqs/sop/move-messages-between-queues/2021-03-11/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-MoveSQSMessagesBetweenQueuesSOP_2021-03-11" SSM document
    And cache number of messages in queue as "SourceNumberOfMessages" "before" SSM automation execution
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And cache number of messages in queue as "TargetNumberOfMessages" "before" SSM automation execution
      | QueueUrl                                             |
      | {{cfn-output:SqsTemplate>SqsDlqForStandardQueueUrl}} |
    And send "1000" messages to queue
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And SSM automation document "Digito-MoveSQSMessagesBetweenQueuesSOP_2021-03-11" executed
      | SourceQueueUrl                                 | TargetQueueUrl                                       | AutomationAssumeRole                                                                        | MessagesTransferBatchSize | NumberOfMessagesToTransfer | ForceExecution |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} | {{cfn-output:SqsTemplate>SqsDlqForStandardQueueUrl}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoMoveSQSMessagesBetweenQueuesSOPAssumeRole}} | 10                        | 1000                       | false          |

    When SSM automation document "Digito-MoveSQSMessagesBetweenQueuesSOP_2021-03-11" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And sleep for "60" seconds
    And cache number of messages in queue as "SourceNumberOfMessages" "after" SSM automation execution
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And cache number of messages in queue as "TargetNumberOfMessages" "after" SSM automation execution
      | QueueUrl                                             |
      | {{cfn-output:SqsTemplate>SqsDlqForStandardQueueUrl}} |
    And purge the queue
      | QueueUrl                                             |
      | {{cfn-output:SqsTemplate>SqsDlqForStandardQueueUrl}} |


    Then assert "SourceNumberOfMessages" at "before" became equal to "SourceNumberOfMessages" at "after"
    And assert the difference between "TargetNumberOfMessages" at "after" and "TargetNumberOfMessages" at "before" became "1000"

