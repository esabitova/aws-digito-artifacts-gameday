@sqs @integration @alarm
Feature: Alarm Setup - sqs SentMessageSize
  Scenario: Check how SentMessageSize not became close to allowed Threshold
    Given the cloud formation templates as integration test resources
      |CfnTemplatePath                                                    | ResourceType
      |resource_manager/cloud_formation_templates/SqsTemplate.yml         | ON_DEMAND
      |resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml | SHARED
    And purge the queue
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |

    When alarm "sqs:alarm:health_alarm_sent_message_size:2020-11-26" is installed
      | alarmId    | SNSTopicARN                       |QueueName                                       | Threshold     |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} |{{cfn-output:SqsTemplate>SqsStandardQueueName}} | 100           |
    And send "10" messages to queue
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    Then assert metrics for all alarms are populated
    And Wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 180 seconds, check every 15 seconds


  Scenario: Check how SentMessageSize became close to allowed Threshold
    Given the cloud formation templates as integration test resources
      |CfnTemplatePath                                                    | ResourceType
      |resource_manager/cloud_formation_templates/SqsTemplate.yml         | ON_DEMAND
      |resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml | SHARED
    And purge the queue
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |

    When alarm "sqs:alarm:health_alarm_sent_message_size:2020-11-26" is installed
      | alarmId    | SNSTopicARN                       |QueueName                                       | Threshold    |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} |{{cfn-output:SqsTemplate>SqsStandardQueueName}} | 10           |
    And send "10" messages to queue
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    Then assert metrics for all alarms are populated
    And Wait until alarm {{alarm:under_test>AlarmName}} becomes ALARM within 180 seconds, check every 15 seconds


