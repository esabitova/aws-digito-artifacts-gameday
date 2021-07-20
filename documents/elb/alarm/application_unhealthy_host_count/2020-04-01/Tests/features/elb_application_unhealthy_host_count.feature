@elb @integration @alarm
Feature: Alarm Setup - application load-balancer UnHealthyHostCount

  Scenario: Alarm is not triggered when count of application load balancer unhealthy hosts less than a threshold - green
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                       | ResourceType
      | resource_manager/cloud_formation_templates/ApplicationELBTemplate.yml | ON_DEMAND
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml    | SHARED
    When alarm "elb:alarm:application_unhealthy_host_count:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | ApplicationELBArn                                            | Threshold | MaxTimeMinutes
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:ApplicationELBTemplate>ApplicationELBFullName}} | 1000      | 1
    Then wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 180 seconds, check every 15 seconds


