@sqs
Feature: SSM automation document to test SQS message size get close to threshold

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                           | ResourceType |
      | resource_manager/cloud_formation_templates/SqsTemplate.yml                                | ON_DEMAND    |
      | documents/sqs/test/capacity_failure/2021-03-13/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And purge the queue
      | QueueUrl                                   |
      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} |
    And SSM automation document "Digito-SQSCapacityFailure_2021-03-13" executed
      | QueueUrl                                   | AutomationAssumeRole                                                           | SentMessageSizeAlarmName                                 |
      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoSQSCapacityFailureAssumeRole}} | {{cfn-output:SqsTemplate>SentMessageSizeFifoQueueAlarm}} |

    When SSM automation document "Digito-SQSCapacityFailure_2021-03-13" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
