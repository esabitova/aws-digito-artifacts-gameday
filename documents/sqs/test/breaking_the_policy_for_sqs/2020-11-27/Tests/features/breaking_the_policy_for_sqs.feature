@sqs
Feature: SSM automation document to to test behavior when messages cannot be sent to an SQS queue

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document to test behavior when messages cannot be sent to an SQS queue
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                      | ResourceType |
      | resource_manager/cloud_formation_templates/SqsTemplate.yml                                           | ON_DEMAND    |
      | documents/sqs/test/breaking_the_policy_for_sqs/2020-11-27/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And SSM automation document "Digito-BreakingThePolicyForSQS_2020-11-27" executed
      | QueueUrl                                       | AutomationAssumeRole                                                                | SQSUserErrorAlarmName                                                |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoBreakingThePolicyForSQSAssumeRole}} | {{cfn-output:SqsTemplate>NumberOfMessagesSentAlarm}} |

    When sleep for "10" seconds
    And send "10" messages to queue
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And Wait for the SSM automation document "Digito-BreakingThePolicyForSQS_2020-11-27" execution is on step "RollbackCurrentExecution" in status "Success" for "1000" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And sleep for "10" seconds
    And send "10" messages to queue
      | QueueUrl                                                                                           |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And SSM automation document "Digito-BreakingThePolicyForSQS_2020-11-27" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |