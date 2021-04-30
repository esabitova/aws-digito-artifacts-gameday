@sqs
Feature: SSM automation document to test behavior of Standard Queue after receiving a message maximum allowed times

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document to test behavior of standard queue after receiving a message maximum allowed times
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
    And purge the queue
      | QueueUrl                                             |
      | {{cfn-output:SqsTemplate>SqsDlqForStandardQueueUrl}} |
    And purge the queue
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And sleep for "60" seconds
    And cache number of messages in queue as "NumberOfMessagesDLQ" "before" SSM automation execution
      | QueueUrl                                             |
      | {{cfn-output:SqsTemplate>SqsDlqForStandardQueueUrl}} |
    And SSM automation document "Digito-QueueStateFailureDlqStandard_2020-11-27" executed
      | QueueUrl                                       | AutomationAssumeRole                                                                     | DeadLetterQueueAlarmName                                |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoQueueStateFailureDlqStandardAssumeRole}} | {{cfn-output:SqsTemplate>DlqMessageStandardQueueAlarm}} |
    And send "100" messages to queue
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |

    When SSM automation document "Digito-QueueStateFailureDlqStandard_2020-11-27" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And sleep for "60" seconds
    And cache visibility timeout as "VisibilityTimeout" "after" SSM automation execution
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And cache redrive policy as "RedrivePolicy" "after" SSM automation execution
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And cache number of messages in queue as "NumberOfMessages" "after" SSM automation execution
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And cache number of messages in queue as "NumberOfMessagesDLQ" "after" SSM automation execution
      | QueueUrl                                             |
      | {{cfn-output:SqsTemplate>SqsDlqForStandardQueueUrl}} |
    And purge the queue
      | QueueUrl                                             |
      | {{cfn-output:SqsTemplate>SqsDlqForStandardQueueUrl}} |
    And purge the queue
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And sleep for "60" seconds


    Then assert "VisibilityTimeout" at "before" became equal to "VisibilityTimeout" at "after"
    And assert "RedrivePolicy" at "before" became equal to "RedrivePolicy" at "after"
    And assert "NumberOfMessages" at "after" became equal to "100"
    And assert "NumberOfMessagesDLQ" at "before" became equal to "NumberOfMessagesDLQ" at "after"