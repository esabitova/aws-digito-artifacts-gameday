@elb @integration @alarm
Feature: Alarm Setup - load balancer HTTPCode_ELB_5XX_Count
  Scenario: Alarm is not triggered when count of http 5xx responses received by load balancer is less than a threshold - green
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                       | ResourceType
      | resource_manager/cloud_formation_templates/ApplicationELBTemplate.yml | ON_DEMAND
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml    | SHARED
    When alarm "elb:alarm:application_httpcode_elb_5xx_count:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | ApplicationELBArn                                            | Threshold | MaxTimeMinutes
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:ApplicationELBTemplate>ApplicationELBFullName}} | 1000      | 1
    Then wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 180 seconds, check every 15 seconds


