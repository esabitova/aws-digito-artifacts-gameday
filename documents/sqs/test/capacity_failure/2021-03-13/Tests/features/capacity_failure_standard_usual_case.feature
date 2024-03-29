@sqs
Feature: SSM automation document to test SQS message size get close to threshold

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                           | ResourceType |
      | resource_manager/cloud_formation_templates/SqsTemplate.yml                                | ON_DEMAND    |
      | documents/sqs/test/capacity_failure/2021-03-13/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-ForceSQSCapacityFailureTest_2021-03-13" SSM document
    And purge the queue
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And cache number of messages in queue as "NumberOfMessages" "before" SSM automation execution
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And SSM automation document "Digito-ForceSQSCapacityFailureTest_2021-03-13" executed
      | QueueUrl                                       | AutomationAssumeRole                                                                    | SentMessageSizeAlarmName                                     |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoForceSQSCapacityFailureTestAssumeRole}} | {{cfn-output:SqsTemplate>SentMessageSizeStandardQueueAlarm}} |

    When SSM automation document "Digito-ForceSQSCapacityFailureTest_2021-03-13" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache number of messages in queue as "NumberOfMessages" "after" SSM automation execution
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |

    Then assert "NumberOfMessages" at "before" became equal to "NumberOfMessages" at "after"
    And assert "NumberOfMessages" at "after" became equal to "0"
