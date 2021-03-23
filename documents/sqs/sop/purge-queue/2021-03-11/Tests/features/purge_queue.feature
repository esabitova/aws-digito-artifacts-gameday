@sqs
Feature: SSM automation document to clean up SQS queue

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document to clean up SQS queue
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                     | ResourceType |
      | resource_manager/cloud_formation_templates/SqsTemplate.yml                           | ON_DEMAND    |
      | documents/sqs/sop/purge-queue/2021-03-11/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And SSM automation document "Digito-PurgeQueue_2021-03-11" executed
      | QueueUrl                                       | AutomationAssumeRole                                                   |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoPurgeQueueAssumeRole}} |


    When SSM automation document "Digito-PurgeQueue_2021-03-11" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |