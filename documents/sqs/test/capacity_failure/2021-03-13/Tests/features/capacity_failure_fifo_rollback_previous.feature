@sqs
Feature: SSM automation document to test SQS message size get close to threshold

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                           | ResourceType |
      | resource_manager/cloud_formation_templates/SqsTemplate.yml                                | ON_DEMAND    |
      | documents/sqs/test/capacity_failure/2021-03-13/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-ForceSQSCapacityFailureTest_2021-03-13" SSM document
    And purge the queue
      | QueueUrl                                   |
      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} |
    And cache number of messages in queue as "NumberOfMessages" "before" SSM automation execution
      | QueueUrl                                   |
      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} |
    And SSM automation document "Digito-ForceSQSCapacityFailureTest_2021-03-13" executed
      | QueueUrl                                   | AutomationAssumeRole                                                                    | SentMessageSizeAlarmName                                 |
      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoForceSQSCapacityFailureTestAssumeRole}} | {{cfn-output:SqsTemplate>SentMessageSizeFifoQueueAlarm}} |

    # Terminate execution before rollback
    When Wait for the SSM automation document "Digito-ForceSQSCapacityFailureTest_2021-03-13" execution is on step "AssertAlarmToBeRed" in status "InProgress"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    Then terminate "Digito-ForceSQSCapacityFailureTest_2021-03-13" SSM automation document
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And Wait for the SSM automation document "Digito-ForceSQSCapacityFailureTest_2021-03-13" execution is on step "TriggerRollback" in status "Success"
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|
    And SSM automation document "Digito-ForceSQSCapacityFailureTest_2021-03-13" execution in status "Cancelled"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And sleep for "60" seconds

    # Wait until alarm goes on
    When Wait for alarm to be in state "ALARM" for "300" seconds
      | AlarmName                                                |
      | {{cfn-output:SqsTemplate>SentMessageSizeFifoQueueAlarm}} |

    # Rollback previous
    Then cache rollback execution id
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|
    When SSM automation document "Digito-ForceSQSCapacityFailureTest_2021-03-13" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>2}} |
    And sleep for "60" seconds
    And cache number of messages in queue as "NumberOfMessages" "after" SSM automation execution
      | QueueUrl                                   |
      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} |

    # Alarm should return to OK
    When Wait for alarm to be in state "OK" for "600" seconds
      | AlarmName                                                |
      | {{cfn-output:SqsTemplate>SentMessageSizeFifoQueueAlarm}} |

    Then assert "NumberOfMessages" at "before" became equal to "NumberOfMessages" at "after"
    And assert "NumberOfMessages" at "after" became equal to "0"
