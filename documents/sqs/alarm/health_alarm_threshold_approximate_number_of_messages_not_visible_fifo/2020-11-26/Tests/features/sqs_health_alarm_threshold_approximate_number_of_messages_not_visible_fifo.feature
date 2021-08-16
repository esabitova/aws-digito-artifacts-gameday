@sqs @integration @alarm
Feature: Alarm Setup - sqs ThresholdApproximateNumberOfMessagesNotVisibleFifo
  Scenario: Check Alarm by Digito that checks that amount of inflight messages is not reaching the quota for Fifo queue - green
    Given the cloud formation templates as integration test resources
      |CfnTemplatePath                                                    | ResourceType
      |resource_manager/cloud_formation_templates/SqsTemplate.yml         | ON_DEMAND
      |resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml | SHARED
    When alarm "sqs:alarm:health_alarm_threshold_approximate_number_of_messages_not_visible_fifo:2020-11-26" is installed
      | alarmId    | SNSTopicARN                       | QueueName                                   | Threshold |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:SqsTemplate>SqsFifoQueueName}} | 20000     |
    And purge the queue
      | QueueUrl                                   |
      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} |
    And send "100" messages with different groups to FIFO queue
      | QueueUrl                                   |
      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} |
    And receive "50" messages from queue
      | QueueUrl                                   |
      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} |
    Then assert metrics for all alarms are populated within 600 seconds, check every 15 seconds
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 300 seconds, check every 15 seconds

  Scenario: Check Alarm by Digito that checks that amount of inflight messages is not reaching the quota for Fifo queue - red
    Given the cloud formation templates as integration test resources
      |CfnTemplatePath                                                    | ResourceType
      |resource_manager/cloud_formation_templates/SqsTemplate.yml         | ON_DEMAND
      |resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml | SHARED
    When alarm "sqs:alarm:health_alarm_threshold_approximate_number_of_messages_not_visible_fifo:2020-11-26" is installed
      | alarmId    | SNSTopicARN                       | QueueName                                   | Threshold |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:SqsTemplate>SqsFifoQueueName}} | 1         |
    And purge the queue
      | QueueUrl                                   |
      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} |
    And send "5" messages with different groups to FIFO queue
      | QueueUrl                                   |
      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} |
    And receive "5" messages from queue
      | QueueUrl                                   | VisibilityTimeout |
      | {{cfn-output:SqsTemplate>SqsFifoQueueUrl}} | 1800              |
    Then assert metrics for all alarms are populated within 600 seconds, check every 15 seconds
    And wait until alarm {{alarm:under_test>AlarmName}} becomes ALARM within 300 seconds, check every 15 seconds
