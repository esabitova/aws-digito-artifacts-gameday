@sqs
Feature: SSM automation document to to test behavior when messages cannot be sent to an SQS queue

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document to test behavior when messages cannot be sent to an SQS queue
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                             | ResourceType |
      | resource_manager/cloud_formation_templates/SqsTemplate.yml                                  | ON_DEMAND    |
      | documents/sqs/test/break_queue_policy/2020-11-27/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-BreakSQSQueuePolicyTest_2020-11-27" SSM document
    And cache queue url as "QueueUrl" "before" SSM automation execution for teardown
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And cache policy as "Policy" "before" SSM automation execution
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And purge the queue
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And cache number of messages in queue as "NumberOfMessages" "before" SSM automation execution
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And SSM automation document "Digito-BreakSQSQueuePolicyTest_2020-11-27" executed
      | QueueUrl                                       | AutomationAssumeRole                                                                | SQSUserErrorAlarmName                                |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoBreakSQSQueuePolicyTestAssumeRole}} | {{cfn-output:SqsTemplate>NumberOfMessagesSentAlarm}} |

    # Keep sending messages long enough so SSM times out if sending is not stopped by access denied error
    And send messages for "2400" seconds until access denied
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |

    # Once sending messages stops it may take up to 2 mins to update alarm
    # This step should not be reached if access denied error was not caught
    When Wait for the SSM automation document "Digito-BreakSQSQueuePolicyTest_2020-11-27" execution is on step "AssertAlarmToBeRed" in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    # Keep sending more messages ignoring access denied errors until policy propagates and SSM execution finishes
    And send messages for "600" seconds ignoring access denied until "5" sent successfully
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |

    And SSM automation document "Digito-BreakSQSQueuePolicyTest_2020-11-27" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And sleep for "60" seconds
    And cache number of messages in queue as "NumberOfMessages" "after" SSM automation execution
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And cache policy as "Policy" "after" SSM automation execution
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |

    Then assert "NumberOfMessages" at "before" became not equal to "NumberOfMessages" at "after"
    And assert "Policy" at "before" became equal to "Policy" at "after"