@elb @integration @alarm
Feature: Alarm Setup - load-balancer LambdaInternalError

  Scenario: Alarm is not triggered when count of lambda internal errors from lambda targets is less than a threshold
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                       | ResourceType
      | resource_manager/cloud_formation_templates/ApplicationELBTemplate.yml | ON_DEMAND
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml    | SHARED
    When alarm "elb:alarm:application_lambda_internal_error:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | ApplicationELBArn                                            | Threshold | MaxTimeMinutes
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:ApplicationELBTemplate>ApplicationELBFullName}} | 1000      | 1
    And invoke lambda "{{cfn-output:ApplicationELBTemplate>ProxyLambdaArn}}" with parameters
      | host             | {{cfn-output:ApplicationELBTemplate>ApplicationELBUrl}} |
      | path             | /invoke_lambda/trigger_error                                            |
      | request_count    | 5                                                       |
      | request_interval | 1                                                       |
    And sleep for "60" seconds
    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 180 seconds, check every 15 seconds


