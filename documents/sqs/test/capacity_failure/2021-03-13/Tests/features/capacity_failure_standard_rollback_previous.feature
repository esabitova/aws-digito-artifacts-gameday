@sqs
Feature: SSM automation document to test SQS message size get close to threshold

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                           | ResourceType |
      | resource_manager/cloud_formation_templates/SqsTemplate.yml                                | ON_DEMAND    |
      | documents/sqs/test/capacity_failure/2021-03-13/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-SQSCapacityFailure_2021-03-13" SSM document
    And purge the queue
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And sleep for "60" seconds
    And cache number of messages in queue as "NumberOfMessages" "before" SSM automation execution
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And SSM automation document "Digito-SQSCapacityFailure_2021-03-13" executed
      | QueueUrl                                       | AutomationAssumeRole                                                           | SentMessageSizeAlarmName                                     |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoSQSCapacityFailureAssumeRole}} | {{cfn-output:SqsTemplate>SentMessageSizeStandardQueueAlarm}} |

    # Terminate execution before rollback
    When Wait for the SSM automation document "Digito-SQSCapacityFailure_2021-03-13" execution is on step "AssertAlarmToBeRed" in status "InProgress" for "600" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    Then terminate "Digito-SQSCapacityFailure_2021-03-13" SSM automation document
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    When SSM automation document "Digito-SQSCapacityFailure_2021-03-13" execution in status "Cancelled"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And sleep for "60" seconds
    And cache number of messages in queue as "NumberOfMessages" "after-send" SSM automation execution
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |

    # Wait until alarm goes on
    When Wait for alarm to be in state "ALARM" for "300" seconds
      | AlarmName                                                    |
      | {{cfn-output:SqsTemplate>SentMessageSizeStandardQueueAlarm}} |

    # Rollback previous
    When SSM automation document "Digito-SQSCapacityFailure_2021-03-13" executed
      | QueueUrl                                       | AutomationAssumeRole                                                           | SentMessageSizeAlarmName                                     | IsRollback | PreviousExecutionId        |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoSQSCapacityFailureAssumeRole}} | {{cfn-output:SqsTemplate>SentMessageSizeStandardQueueAlarm}} | true       | {{cache:SsmExecutionId>1}} |
    And SSM automation document "Digito-SQSCapacityFailure_2021-03-13" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>2}} |
    And sleep for "60" seconds
    And cache number of messages in queue as "NumberOfMessages" "after" SSM automation execution
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |

    # Alarm should return to OK
    When Wait for alarm to be in state "OK" for "600" seconds
      | AlarmName                                                    |
      | {{cfn-output:SqsTemplate>SentMessageSizeStandardQueueAlarm}} |

    Then assert "NumberOfMessages" at "before" became equal to "NumberOfMessages" at "after"
    And assert "NumberOfMessages" at "after-send" became not equal to "NumberOfMessages" at "before"
    And assert "NumberOfMessages" at "after" became equal to "0"
