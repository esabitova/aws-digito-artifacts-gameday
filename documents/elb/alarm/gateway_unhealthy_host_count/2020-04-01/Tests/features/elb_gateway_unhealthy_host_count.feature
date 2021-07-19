@elb @integration @alarm
Feature: Alarm Setup - load-balancer UnHealthyHostCount

  Scenario: Alarm is not triggered when count of elb unhealthy hosts less than a threshold - green
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                            | ResourceType
      | resource_manager/cloud_formation_templates/GatewayLoadBalancerTemplate.yml | ON_DEMAND
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml         | SHARED
    When alarm "elb:alarm:gateway_unhealthy_host_count:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | ApplicationELBArn                                             | Threshold | MaxTimeMinutes
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:GatewayLoadBalancerTemplate>GatewayELBFullName}} | 1000      | 1
    Then wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 180 seconds, check every 15 seconds


