@sqs @integration @alarm
Feature: Alarm Setup - sqs ApproximateAgeOfOldestMessageDLQ
  Scenario: Check age of the oldest message in DLQ - green
    Given the cloud formation templates as integration test resources
      |CfnTemplatePath                                                    | ResourceType
      |resource_manager/cloud_formation_templates/SqsTemplate.yml         | ON_DEMAND
      |resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml | SHARED
    And purge the queue
      | QueueUrl                                             |
      | {{cfn-output:SqsTemplate>SqsDlqForStandardQueueUrl}} |
    # set threshold to a value more then timeout of our alarm check which is 900 secs
    When alarm "sqs:alarm:recovery_alarm_approximate_age_of_oldest_message_dlq:2020-11-26" is installed
      | alarmId    | SNSTopicARN                       | QueueName                                             | Threshold |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:SqsTemplate>SqsDlqForStandardQueueName}} | 10000     |
    And send "10" messages to queue
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsDlqForStandardQueueUrl}} |
    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 900 seconds, check every 15 seconds

  Scenario: Check age of the oldest message in DLQ - red
    Given the cloud formation templates as integration test resources
      |CfnTemplatePath                                                    | ResourceType
      |resource_manager/cloud_formation_templates/SqsTemplate.yml         | ON_DEMAND
      |resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml | SHARED
    And purge the queue
      | QueueUrl                                             |
      | {{cfn-output:SqsTemplate>SqsDlqForStandardQueueUrl}} |
    # set threshold to a value less then timeout of our alarm check which is 900 secs
    When alarm "sqs:alarm:recovery_alarm_approximate_age_of_oldest_message_dlq:2020-11-26" is installed
      | alarmId    | SNSTopicARN                       | QueueName                                             | Threshold |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:SqsTemplate>SqsDlqForStandardQueueName}} | 1         |
    And send "10" messages to queue
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsDlqForStandardQueueUrl}} |
    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes ALARM within 900 seconds, check every 15 seconds
