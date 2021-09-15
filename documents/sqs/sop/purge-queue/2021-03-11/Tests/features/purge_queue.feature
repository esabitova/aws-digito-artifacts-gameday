@sqs
Feature: SSM automation document to clean up SQS queue

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document to clean up SQS queue
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                     | ResourceType |
      | resource_manager/cloud_formation_templates/SqsTemplate.yml                          | ON_DEMAND    |
      | documents/sqs/sop/purge-queue/2021-03-11/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-PurgeSQSQueueSOP_2021-03-11" SSM document
    And purge the queue
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And send "25" messages to queue
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    # sleep before PurgeQueue execution by Digito-PurgeSQSQueueSOP_2021-03-11
    And sleep for "60" seconds
    And cache number of messages in queue as "NumberOfMessages" "before" SSM automation execution
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And SSM automation document "Digito-PurgeSQSQueueSOP_2021-03-11" executed
      | QueueUrl                                       | AutomationAssumeRole                                                         |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoPurgeSQSQueueSOPAssumeRole}} |

    When SSM automation document "Digito-PurgeSQSQueueSOP_2021-03-11" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache number of messages in queue as "NumberOfMessages" "after" SSM automation execution
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |

    Then assert "NumberOfMessages" at "before" became not equal to "NumberOfMessages" at "after"
    And assert "NumberOfMessages" at "after" became equal to "0"
