@sqs @integration @alarm
Feature: Alarm Setup - sqs ThresholdApproximateNumberOfMessagesNotVisibleStandardQueue
  Scenario: Check Alarm by Digito that checks that amount of inflight messages is not reaching the quota for Standard queue - green
    Given the cloud formation templates as integration test resources
      |CfnTemplatePath                                                    | ResourceType
      |resource_manager/cloud_formation_templates/SqsTemplate.yml         | ON_DEMAND
      |resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml | SHARED
    When alarm "sqs:alarm:health_alarm_threshold_approximate_number_of_messages_not_visible_standard_queue:2020-11-26" is installed
      | alarmId    | SNSTopicARN                       | QueueName                                       | Threshold |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:SqsTemplate>SqsStandardQueueName}} | 120000    |
    # purging api has a max calls within 10 seconds, so sleep to guarantee the purging
    And sleep for "60" seconds
    And purge the queue
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And send "100" messages to queue
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And receive "50" messages from queue
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    Then assert metrics for all alarms are populated within 1200 seconds, check every 15 seconds
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 300 seconds, check every 15 seconds

  Scenario: Check Alarm by Digito that checks that amount of inflight messages is not reaching the quota for Standard queue - red
    Given the cloud formation templates as integration test resources
      |CfnTemplatePath                                                    | ResourceType
      |resource_manager/cloud_formation_templates/SqsTemplate.yml         | ON_DEMAND
      |resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml | SHARED
    When alarm "sqs:alarm:health_alarm_threshold_approximate_number_of_messages_not_visible_standard_queue:2020-11-26" is installed
      | alarmId    | SNSTopicARN                       | QueueName                                       | Threshold |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:SqsTemplate>SqsStandardQueueName}} | 10        |
    # purging api has a max calls within 10 seconds, so sleep to guarantee the purging
    And sleep for "60" seconds
    And purge the queue
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And send "100" messages to queue
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And receive "50" messages from queue
      | QueueUrl                                       | VisibilityTimeout |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} | 1800              |
    Then assert metrics for all alarms are populated within 1200 seconds, check every 15 seconds
    And wait until alarm {{alarm:under_test>AlarmName}} becomes ALARM within 300 seconds, check every 15 seconds
