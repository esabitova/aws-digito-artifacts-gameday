@sqs @integration @alarm
Feature: Alarm Setup - sqs ApproximateAgeOfOldestMessageMaximum
  Scenario: Check age of the oldest message - green
    Given the cloud formation templates as integration test resources
      |CfnTemplatePath                                                    | ResourceType
      |resource_manager/cloud_formation_templates/SqsTemplate.yml         | ON_DEMAND
      |resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml | SHARED
    # purging api has a max calls within 10 seconds, so sleep to guarantee the purging
    And sleep for "10" seconds
    And purge the queue
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    When alarm "sqs:alarm:health_alarm_approximate_age_of_oldest_message_maximum:2020-11-26" is installed
      | alarmId    | SNSTopicARN                       | QueueName                                      | Threshold
      | under_test | {{cfn-output:SnsForAlarms>Topic}} |{{cfn-output:SqsTemplate>SqsStandardQueueName}} | 15
    And send "10" messages to queue
      | QueueUrl                                          |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |

    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 180 seconds, check every 15 seconds

  Scenario: Check age of the oldest message - red
    Given the cloud formation templates as integration test resources
      |CfnTemplatePath                                                    | ResourceType
      |resource_manager/cloud_formation_templates/SqsTemplate.yml         | ON_DEMAND
      |resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml | SHARED
    # purging api has a max calls within 10 seconds, so sleep to guarantee the purging
    And sleep for "10" seconds
    And purge the queue
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    When alarm "sqs:alarm:health_alarm_approximate_age_of_oldest_message_maximum:2020-11-26" is installed
      | alarmId    | SNSTopicARN                       | QueueName                                      | Threshold
      | under_test | {{cfn-output:SnsForAlarms>Topic}} |{{cfn-output:SqsTemplate>SqsStandardQueueName}} | 1
    And send "10" messages to queue
      | QueueUrl                                             |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |

    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes ALARM within 180 seconds, check every 15 seconds


