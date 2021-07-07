@sqs @integration @alarm
Feature: Alarm Setup - sqs DLQMessage
  Scenario: Is there any message in DLQ - green
    Given the cloud formation templates as integration test resources
      |CfnTemplatePath                                                    | ResourceType
      |resource_manager/cloud_formation_templates/SqsTemplate.yml         | ON_DEMAND
      |resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml | SHARED
    # only one PurgeQueue is allowed in 60 seconds
    And sleep for "60" seconds
    And purge the queue
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And purge the queue
      | QueueUrl                                             |
      | {{cfn-output:SqsTemplate>SqsDlqForStandardQueueUrl}} |

    When alarm "sqs:alarm:health_alarm_dlq_message:2020-11-26" is installed
      | alarmId    | SNSTopicARN                       | QueueName                                             | Threshold |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:SqsTemplate>SqsDlqForStandardQueueName}} | 0         |
    And send "10" messages to queue
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |

    Then assert metrics for all alarms are populated
    And sleep for "30" seconds
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 180 seconds, check every 15 seconds

  Scenario: Is there any message in DLQ - red
    Given the cloud formation templates as integration test resources
      |CfnTemplatePath                                                    | ResourceType
      |resource_manager/cloud_formation_templates/SqsTemplate.yml         | ON_DEMAND
      |resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml | SHARED
    # only one PurgeQueue is allowed in 60 seconds
    And sleep for "60" seconds
    And purge the queue
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsStandardQueueUrl}} |
    And purge the queue
      | QueueUrl                                             |
      | {{cfn-output:SqsTemplate>SqsDlqForStandardQueueUrl}} |

    When alarm "sqs:alarm:health_alarm_dlq_message:2020-11-26" is installed
      | alarmId    | SNSTopicARN                       | QueueName                                             | Threshold |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:SqsTemplate>SqsDlqForStandardQueueName}} | 0         |
    And send "10" messages to queue
      | QueueUrl                                       |
      | {{cfn-output:SqsTemplate>SqsDlqForStandardQueueUrl}} |

    Then assert metrics for all alarms are populated
    And sleep for "30" seconds
    And wait until alarm {{alarm:under_test>AlarmName}} becomes ALARM within 180 seconds, check every 15 seconds
