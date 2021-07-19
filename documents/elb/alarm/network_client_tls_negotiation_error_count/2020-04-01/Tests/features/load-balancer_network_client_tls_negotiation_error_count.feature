@elb @integration @alarm
Feature: Alarm Setup - network load-balancer ClientTLSNegotiationErrorCount

  Scenario: Alarm is not triggered when network client tls negotiation error count is less than a threshold
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                            | ResourceType
      | resource_manager/cloud_formation_templates/NetworkLoadBalancerTemplate.yml | ON_DEMAND
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml         | SHARED
    When alarm "elb:alarm:network_client_tls_negotiation_error_count:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | NetworkELBArn                                                 | Threshold | MaxTimeMinutes
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:NetworkLoadBalancerTemplate>NetworkELBFullName}} | 1000      | 1
    Then wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 180 seconds, check every 15 seconds


