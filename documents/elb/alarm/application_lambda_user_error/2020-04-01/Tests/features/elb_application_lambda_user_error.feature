@elb @integration @alarm
Feature: Alarm Setup - load-balancer LambdaUserError

  Scenario: Alarm is not triggered when count of lambda user errors from lambda targets is less than a threshold
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                       | ResourceType
      | resource_manager/cloud_formation_templates/ApplicationELBTemplate.yml | ON_DEMAND
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml    | SHARED
    When alarm "elb:alarm:application_lambda_user_error:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | LambdaTargetFullName                                       | Threshold | MaxTimeMinutes
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:ApplicationELBTemplate>LambdaTargetFullName}} | 1000      | 1
    And invoke lambda "{{cfn-output:ApplicationELBTemplate>ProxyLambdaArn}}" with parameters
      | host             | {{cfn-output:ApplicationELBTemplate>ApplicationELBUrl}} |
      | path             | /invoke_lambda/trigger_error                            |
      | request_count    | 5                                                       |
      | request_interval | 1                                                       |
    And sleep for "60" seconds
    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 180 seconds, check every 15 seconds

  Scenario: Report when count of lambda user errors from lambda targets is greater than or equal to a threshold - red
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                       | ResourceType
      | resource_manager/cloud_formation_templates/ApplicationELBTemplate.yml | ON_DEMAND
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml    | SHARED
    When alarm "elb:alarm:application_lambda_user_error:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | LambdaTargetFullName                                       | Threshold | MaxTimeMinutes
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:ApplicationELBTemplate>LambdaTargetFullName}} | 1         | 1
    And invoke lambda "{{cfn-output:ApplicationELBTemplate>ProxyLambdaArn}}" with parameters
      | host             | {{cfn-output:ApplicationELBTemplate>ApplicationELBUrl}} |
      | path             | /invoke_lambda/trigger_error                            |
      | request_count    | 5                                                       |
      | request_interval | 1                                                       |
    And sleep for "60" seconds
    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes ALARM within 180 seconds, check every 15 seconds


