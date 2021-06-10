@sqs @integration @alarm
Feature: Alarm Setup - SQS NumberOfMessagesSentBand
  Scenario: To detect anomalies of high and low values of NumberOfMessagesSent
    Given the cloud formation templates as integration test resources
      |CfnTemplatePath                                                    | ResourceType
      |resource_manager/cloud_formation_templates/SqsTemplate.yml         | ON_DEMAND
      |resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml | SHARED
    When alarm "sqs:alarm:health_alarm_number_of_messages_sent_band:2020-11-26" is installed
      | SNSTopicARN                       | QueueName                                  | Threshold
      | {{cfn-output:SnsForAlarms>Topic}} |{{cfn-output:SqsTemplate>SqsFifoQueueName}} | 0.5
    Then assert metrics for all alarms are populated

