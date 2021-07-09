@elb @integration @alarm
Feature: Alarm Setup - application elastic load-balancer ClientTLSNegotiationErrorCount

  Scenario: Alarm is not triggered when application ELB TLS error count is less than a threshold - green
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                       | ResourceType
      | resource_manager/cloud_formation_templates/ApplicationELBTemplate.yml | ON_DEMAND
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml    | SHARED
    When alarm "elb:alarm:application_client_tls_negotiation_error_count:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | ApplicationELBArn                                            | Threshold | MaxTimeMinutes |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:ApplicationELBTemplate>ApplicationELBFullName}} | 1000      | 1              |
    And send incorrect https requests 10 times
      | TestUrl                                                 |
      | {{cfn-output:ApplicationELBTemplate>ApplicationELBUrl}} |
    And sleep for "20" seconds
    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 180 seconds, check every 15 seconds

  Scenario: Alarm reports when application ELB TLS error count is greater or equal to a threshold - red
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                       | ResourceType
      | resource_manager/cloud_formation_templates/ApplicationELBTemplate.yml | ON_DEMAND
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml    | SHARED
    When alarm "elb:alarm:application_client_tls_negotiation_error_count:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | ApplicationELBArn                                            | Threshold | MaxTimeMinutes |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:ApplicationELBTemplate>ApplicationELBFullName}} | 1         | 1              |
    And sleep for "10" seconds
    And send incorrect https requests 10 times
      | TestUrl                                                 |
      | {{cfn-output:ApplicationELBTemplate>ApplicationELBUrl}} |
    And sleep for "20" seconds
    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes ALARM within 180 seconds, check every 15 seconds