@sqs
Feature: SSM automation document to block sqs:DeleteMessage

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document to block sqs:DeleteMessage
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                               | ResourceType |
      | resource_manager/cloud_formation_templates/SqsTemplate.yml                                    | ON_DEMAND    |
      | documents/sqs/test/block_delete_message/2021-03-09/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And purge the queue
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And SSM automation document "Digito-BlockSQSDeleteMessage_2021-03-09" executed
      | QueueUrl                                       | AutomationAssumeRole                                                              |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoBlockSQSDeleteMessageAssumeRole}} |

#    When Wait for the SSM automation document "Digito-BlockSQSDeleteMessage_2021-03-09" execution is on step "AssertAlarmToBeGreenBeforeTest" in status "InProgress" for "1000" seconds
#      | ExecutionId                |
#      | {{cache:SsmExecutionId>1}} |
#     Only one PurgeQueue operation is allowed every 60 seconds.
#    And sleep for "60" seconds
#    And send messages to the SQS queue "5" times
#      | QueueUrl                                       |
#      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
#    And sleep for "40" seconds
#    And receive messages from the SQS queue
#      | QueueUrl                                       |
#      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
#    And purge the queue
#      | QueueUrl                                       |
#      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
#    And sleep for "50" seconds
#    And Wait for the SSM automation document "Digito-BlockSQSDeleteMessage_2021-03-09" execution is on step "AssertAlarmToBeGreenBeforeTest" in status "Success" for "1000" seconds
#      | ExecutionId                |
#      | {{cache:SsmExecutionId>1}} |
    When Wait for the SSM automation document "Digito-BlockSQSDeleteMessage_2021-03-09" execution is on step "UpdatePolicy" in status "Success" for "1000" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And send messages to the SQS queue "5" times
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And Wait for the SSM automation document "Digito-BlockSQSDeleteMessage_2021-03-09" execution is on step "RollbackCurrentExecution" in status "Success" for "1000" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And purge the queue
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And sleep for "60" seconds
    And send messages to the SQS queue "5" times
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And sleep for "40" seconds
    And purge the queue
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And SSM automation document "Digito-BlockSQSDeleteMessage_2021-03-09" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
