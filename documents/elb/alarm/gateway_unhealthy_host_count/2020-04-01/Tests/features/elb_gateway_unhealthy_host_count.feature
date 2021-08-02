@elb @integration @alarm
Feature: Alarm Setup - load-balancer UnHealthyHostCount

  Scenario: Alarm is not triggered when count of elb unhealthy hosts less than a threshold - green
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                            | ResourceType | VPC                      | Subnet                                             | VPCCidr                    |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                  | SHARED       |                          |                                                    |                            |
      | resource_manager/cloud_formation_templates/GatewayLoadBalancerTemplate.yml | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetOne}} | {{cfn-output:VPC>VPCCidr}} |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml         | SHARED       |                          |                                                    |                            |
    When alarm "elb:alarm:gateway_unhealthy_host_count:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | GatewayLoadBalancerName                                       | TargetGroup                                            | Threshold | EvaluationPeriods | DatapointsToAlarm |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:GatewayLoadBalancerTemplate>GatewayELBFullName}} | {{cfn-output:GatewayLoadBalancerTemplate>TargetGroup}} | 1000      | 1                 | 1                 |
    Then wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 180 seconds, check every 15 seconds


