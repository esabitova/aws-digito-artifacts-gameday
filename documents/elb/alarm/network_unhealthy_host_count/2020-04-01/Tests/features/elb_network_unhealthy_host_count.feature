@elb @integration @alarm
Feature: Alarm Setup - load-balancer UnHealthyHostCount

  Scenario: Alarm is not triggered when count of elb unhealthy hosts less than a threshold - green
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                            | ResourceType |  VPC                     | Subnet                            | VPCCidr                     |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                  | SHARED       |                          |                                   |                             |
      | resource_manager/cloud_formation_templates/NetworkLoadBalancerTemplate.yml | ON_DEMAND    | {{cfn-output:VPC>VPCId}} |{{cfn-output:VPC>PublicSubnetOne}} | {{cfn-output:VPC>VPCCidr}}  |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml         | SHARED       |                          |                                   |                             |
    When alarm "elb:alarm:network_unhealthy_host_count:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | NetworkLoadBalancerName                                       | TargetGroup                                            | Threshold | EvaluationPeriods | DatapointsToAlarm |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:NetworkLoadBalancerTemplate>NetworkELBFullName}} | {{cfn-output:NetworkLoadBalancerTemplate>TargetGroup}} | 1000      | 1                 | 1                 |
    Then wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 180 seconds, check every 15 seconds


