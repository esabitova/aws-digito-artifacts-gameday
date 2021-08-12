@sqs @integration @alarm
Feature: Alarm Setup - sqs ApproximateAgeOfOldestMessageDLQ
  Scenario: Check age of the oldest message in DLQ - green
    Given the cloud formation templates as integration test resources
      |CfnTemplatePath                                                    | ResourceType
      |resource_manager/cloud_formation_templates/SqsTemplate.yml         | ON_DEMAND
      |resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml | SHARED
    # purging api has a max calls within 60 seconds, so sleep to guarantee the purging
    And sleep for "60" seconds
    And purge the queue
      | QueueUrl                                             |
      | {{cfn-output:SqsTemplate>SqsDlqForStandardQueueUrl}} |
    # set threshold to a value more then timeout of our alarm check which is 180 secs
    When alarm "sqs:alarm:recovery_alarm_approximate_age_of_oldest_message_dlq:2020-11-26" is installed
      | alarmId    | SNSTopicARN                       | QueueName                                             | Threshold |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:SqsTemplate>SqsDlqForStandardQueueName}} | 300       |
    And send "10" messages to queue
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsDlqForStandardQueueUrl}} |
    Then assert metrics for all alarms are populated within 1200 seconds, check every 15 seconds
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 300 seconds, check every 15 seconds

  Scenario: Check age of the oldest message in DLQ - red
    Given the cloud formation templates as integration test resources
      |CfnTemplatePath                                                    | ResourceType
      |resource_manager/cloud_formation_templates/SqsTemplate.yml         | ON_DEMAND
      |resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml | SHARED
    # purging api has a max calls within 60 seconds, so sleep to guarantee the purging
    And sleep for "60" seconds
    And purge the queue
      | QueueUrl                                             |
      | {{cfn-output:SqsTemplate>SqsDlqForStandardQueueUrl}} |
    # set threshold to a value more then timeout of our alarm check which is 180 secs
    When alarm "sqs:alarm:recovery_alarm_approximate_age_of_oldest_message_dlq:2020-11-26" is installed
      | alarmId    | SNSTopicARN                       | QueueName                                             | Threshold |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:SqsTemplate>SqsDlqForStandardQueueName}} | 30        |
    And send "10" messages to queue
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsDlqForStandardQueueUrl}} |
    Then assert metrics for all alarms are populated within 1200 seconds, check every 15 seconds
    And wait until alarm {{alarm:under_test>AlarmName}} becomes ALARM within 300 seconds, check every 15 seconds
