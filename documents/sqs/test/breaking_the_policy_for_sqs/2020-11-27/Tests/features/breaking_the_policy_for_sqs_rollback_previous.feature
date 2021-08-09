@sqs
Feature: SSM automation document to to test behavior when messages cannot be sent to an SQS queue

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document to test behavior when messages cannot be sent to an SQS queue
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                      | ResourceType |
      | resource_manager/cloud_formation_templates/SqsTemplate.yml                                           | ON_DEMAND    |
      | documents/sqs/test/breaking_the_policy_for_sqs/2020-11-27/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-BreakingThePolicyForSQS_2020-11-27" SSM document
    And cache queue url as "QueueUrl" "before" SSM automation execution for teardown
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And cache policy as "Policy" "before" SSM automation execution
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    # only one PurgeQueue is allowed during 60 seconds
    And sleep for "60" seconds
    And purge the queue
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And SSM automation document "Digito-BreakingThePolicyForSQS_2020-11-27" executed
      | QueueUrl                                       | AutomationAssumeRole                                                                | SQSUserErrorAlarmName                                |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoBreakingThePolicyForSQSAssumeRole}} | {{cfn-output:SqsTemplate>NumberOfMessagesSentAlarm}} |

    # Keep sending messages long enough so SSM times out if sending is not stopped by access denied error
    And send messages for "1200" seconds until access denied
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |

    # Terminate execution
    When Wait for the SSM automation document "Digito-BreakingThePolicyForSQS_2020-11-27" execution is on step "UpdateQueuePolicy" in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    Then terminate "Digito-BreakingThePolicyForSQS_2020-11-27" SSM automation document
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    And cache policy as "Policy" "after-terminate" SSM automation execution
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |

    And Wait for the SSM automation document "Digito-BreakingThePolicyForSQS_2020-11-27" execution is on step "TriggerRollback" in status "Success"
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|
    And SSM automation document "Digito-BreakingThePolicyForSQS_2020-11-27" execution in status "Cancelled"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    # Check policy
    When Wait for alarm to be in state "ALARM" for "600" seconds
      | AlarmName                                            |
      | {{cfn-output:SqsTemplate>NumberOfMessagesSentAlarm}} |

    # Run rollback
    Then cache rollback execution id
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|
    When SSM automation document "Digito-BreakingThePolicyForSQS_2020-11-27" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>2}} |

    And send messages for "600" seconds ignoring access denied until "5" sent successfully
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And Wait for alarm to be in state "OK" for "50" seconds
      | AlarmName                                            |
      | {{cfn-output:SqsTemplate>NumberOfMessagesSentAlarm}} |
    And sleep for "60" seconds
    And cache policy as "Policy" "after" SSM automation execution
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |

    Then assert "Policy" at "before" became not equal to "Policy" at "after-terminate"
    And assert "Policy" at "before" became equal to "Policy" at "after"