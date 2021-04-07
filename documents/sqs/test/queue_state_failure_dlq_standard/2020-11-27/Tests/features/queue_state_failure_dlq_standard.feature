@sqs
Feature: SSM automation document to test behavior of Standard Queue after receiving a message maximum allowed times

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document to test behavior of standard queue after receiving a message maximum allowed times
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                           | ResourceType |
      | resource_manager/cloud_formation_templates/SqsTemplate.yml                                                | ON_DEMAND    |
      | documents/sqs/test/queue_state_failure_dlq_standard/2020-11-27/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-QueueStateFailureDlqStandard_2020-11-27" SSM document
    And SSM automation document "Digito-QueueStateFailureDlqStandard_2020-11-27" executed
      | QueueUrl                                       | AutomationAssumeRole                                                                     | DeadLetterQueueAlarmName                                |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoQueueStateFailureDlqStandardAssumeRole}} | {{cfn-output:SqsTemplate>DlqMessageStandardQueueAlarm}} |

    When SSM automation document "Digito-QueueStateFailureDlqStandard_2020-11-27" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

