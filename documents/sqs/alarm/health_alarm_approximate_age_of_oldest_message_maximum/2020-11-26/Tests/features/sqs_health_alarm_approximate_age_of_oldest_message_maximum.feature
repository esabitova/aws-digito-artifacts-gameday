@sqs @integration @alarm
Feature: Alarm Setup - sqs ApproximateAgeOfOldestMessageMaximum

  Scenario: Check age of the oldest message - green
    Given the cloud formation templates as integration test resources
      |CfnTemplatePath                                                    | ResourceType
      |resource_manager/cloud_formation_templates/SqsTemplate.yml         | ON_DEMAND
      |resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml | SHARED
    And purge the queue
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    # Set the high threshold to have OK status of the alarm
    When alarm "sqs:alarm:health_alarm_approximate_age_of_oldest_message_maximum:2020-11-26" is installed
      | alarmId    | SNSTopicARN                       | QueueName                                       | Threshold
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:SqsTemplate>SqsStandardQueueName}} | 10000
    And send "10" messages to queue
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |

    Then assert metrics for all alarms are populated within 1200 seconds, check every 15 seconds
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 180 seconds, check every 15 seconds

  Scenario: Check age of the oldest message - red
    Given the cloud formation templates as integration test resources
      |CfnTemplatePath                                                    | ResourceType
      |resource_manager/cloud_formation_templates/SqsTemplate.yml         | ON_DEMAND
      |resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml | SHARED
    And purge the queue
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    # Set the low threshold to have ALARM status of the alarm
    When alarm "sqs:alarm:health_alarm_approximate_age_of_oldest_message_maximum:2020-11-26" is installed
      | alarmId    | SNSTopicARN                       | QueueName                                      | Threshold
      | under_test | {{cfn-output:SnsForAlarms>Topic}} |{{cfn-output:SqsTemplate>SqsStandardQueueName}} | 1
    And send "10" messages to queue
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |

    Then assert metrics for all alarms are populated within 1200 seconds, check every 15 seconds
    And wait until alarm {{alarm:under_test>AlarmName}} becomes ALARM within 900 seconds, check every 15 seconds


