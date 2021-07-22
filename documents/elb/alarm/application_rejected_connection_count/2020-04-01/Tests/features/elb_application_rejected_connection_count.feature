@elb @integration @alarm
Feature: Alarm Setup - load-balancer RejectedConnectionCount

  Scenario: Alarm is not triggered when application load balancer rejected connections count is less than a threshold
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                       | ResourceType
      | resource_manager/cloud_formation_templates/ApplicationELBTemplate.yml | ON_DEMAND
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml    | SHARED
    When alarm "elb:alarm:application_rejected_connection_count:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | ApplicationLoadBalancerArn                                   | Threshold | MaxTimeMinutes
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:ApplicationELBTemplate>ApplicationELBFullName}} | 1000      | 1
    Then wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 180 seconds, check every 15 seconds
