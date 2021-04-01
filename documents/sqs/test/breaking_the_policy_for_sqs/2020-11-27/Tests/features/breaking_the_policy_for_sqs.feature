@sqs @actual
Feature: SSM automation document to to test behavior when messages cannot be sent to an SQS queue

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document to test behavior when messages cannot be sent to an SQS queue
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                      | ResourceType |
      | resource_manager/cloud_formation_templates/SqsTemplate.yml                                           | ON_DEMAND    |
      | documents/sqs/test/breaking_the_policy_for_sqs/2020-11-27/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-BreakingThePolicyForSQS_2020-11-27" SSM document
    And purge the queue
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And sleep for "60" seconds
    And cache number of messages in queue as "NumberOfMessages" "before" SSM automation execution
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And SSM automation document "Digito-BreakingThePolicyForSQS_2020-11-27" executed
      | QueueUrl                                       | AutomationAssumeRole                                                                | SQSUserErrorAlarmName                                |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoBreakingThePolicyForSQSAssumeRole}} | {{cfn-output:SqsTemplate>NumberOfMessagesSentAlarm}} |

    When Wait for the SSM automation document "Digito-BreakingThePolicyForSQS_2020-11-27" execution is on step "AssertAlarmToBeGreenBeforeTest" in status "InProgress" for "600" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And send "5" messages to queue
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    When Wait for the SSM automation document "Digito-BreakingThePolicyForSQS_2020-11-27" execution is on step "AssertAlarmToBeRed" in status "InProgress" for "600" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    # Try to send some messages until alarm triggers
    And send "5" messages to queue with error
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And sleep for "30" seconds
    And send "5" messages to queue with error
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |

    # Alarm should be triggered despite messages being sent in less than 60 secs after last send attempt
    When Wait for the SSM automation document "Digito-BreakingThePolicyForSQS_2020-11-27" execution is on step "AssertAlarmToBeRed" in status "Success" for "50" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    And Wait for the SSM automation document "Digito-BreakingThePolicyForSQS_2020-11-27" execution is on step "AssertAlarmToBeGreen" in status "InProgress" for "600" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And send "5" messages to queue
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And SSM automation document "Digito-BreakingThePolicyForSQS_2020-11-27" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And sleep for "60" seconds
    And cache number of messages in queue as "NumberOfMessages" "after" SSM automation execution
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And purge the queue
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And sleep for "60" seconds

    Then assert "NumberOfMessages" at "before" became not equal to "NumberOfMessages" at "after"