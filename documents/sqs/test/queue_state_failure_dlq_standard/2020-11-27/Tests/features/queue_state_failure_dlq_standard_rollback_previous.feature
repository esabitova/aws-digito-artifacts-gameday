@sqs
Feature: SSM automation document to test behavior of Standard Queue after receiving a message maximum allowed times

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document to test rollback of previous execution
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                           | ResourceType |
      | resource_manager/cloud_formation_templates/SqsTemplate.yml                                                | ON_DEMAND    |
      | documents/sqs/test/queue_state_failure_dlq_standard/2020-11-27/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-QueueStateFailureDlqStandard_2020-11-27" SSM document
    And cache visibility timeout as "VisibilityTimeout" "before" SSM automation execution
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And cache redrive policy as "RedrivePolicy" "before" SSM automation execution
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And SSM automation document "Digito-QueueStateFailureDlqStandard_2020-11-27" executed
      | QueueUrl                                       | AutomationAssumeRole                                                                     | DeadLetterQueueAlarmName                                |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoQueueStateFailureDlqStandardAssumeRole}} | {{cfn-output:SqsTemplate>DlqMessageStandardQueueAlarm}} |

    When Wait for the SSM automation document "Digito-QueueStateFailureDlqStandard_2020-11-27" execution is on step "ReadMessage" in status "InProgress" for "600" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    Then terminate "Digito-QueueStateFailureDlqStandard_2020-11-27" SSM automation document
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And SSM automation document "Digito-QueueStateFailureDlqStandard_2020-11-27" execution in status "Cancelled"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    When SSM automation document "Digito-QueueStateFailureDlqStandard_2020-11-27" executed
      | QueueUrl                                       | AutomationAssumeRole                                                                     | DeadLetterQueueAlarmName                                | IsRollback | PreviousExecutionId        |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoQueueStateFailureDlqStandardAssumeRole}} | {{cfn-output:SqsTemplate>DlqMessageStandardQueueAlarm}} | True       | {{cache:SsmExecutionId>1}} |

    And SSM automation document "Digito-QueueStateFailureDlqStandard_2020-11-27" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>2}} |
    And cache visibility timeout as "VisibilityTimeout" "after" SSM automation execution
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And cache redrive policy as "RedrivePolicy" "after" SSM automation execution
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |

    Then assert "VisibilityTimeout" at "before" became equal to "VisibilityTimeout" at "after"
    Then assert "RedrivePolicy" at "before" became equal to "RedrivePolicy" at "after"