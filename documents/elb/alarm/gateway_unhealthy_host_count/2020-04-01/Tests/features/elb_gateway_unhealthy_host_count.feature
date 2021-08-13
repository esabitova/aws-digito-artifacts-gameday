@elb @integration @alarm
Feature: Alarm Setup - load-balancer UnHealthyHostCount

  Scenario: Create elb:alarm:gateway_unhealthy_host_count:2020-04-01 based on UnHealthyHostCount metric and check OK status
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                            | ResourceType | VPC                      | Subnet                                             | VPCCidr                    |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                  | SHARED       |                          |                                                    |                            |
      | resource_manager/cloud_formation_templates/GatewayLoadBalancerTemplate.yml | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>PrivateSubnetWithNATGateway}} | {{cfn-output:VPC>VPCCidr}} |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml         | SHARED       |                          |                                                    |                            |
    When alarm "elb:alarm:gateway_unhealthy_host_count:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | GatewayLoadBalancerName                                       | TargetGroup                                            | Threshold | EvaluationPeriods | DatapointsToAlarm |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:GatewayLoadBalancerTemplate>GatewayELBFullName}} | {{cfn-output:GatewayLoadBalancerTemplate>TargetGroup}} | 1000      | 1                 | 1                 |
    And set target group "{{cfn-output:GatewayLoadBalancerTemplate>TargetGroupArn}}" healthcheck port "65534"
    Then assert metrics for all alarms are populated
    Then wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 180 seconds, check every 15 seconds

  Scenario: Create elb:alarm:gateway_unhealthy_host_count:2020-04-01 based on UnHealthyHostCount metric and check ALARM status
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                            | ResourceType | VPC                      | Subnet                                             | VPCCidr                    |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                  | SHARED       |                          |                                                    |                            |
      | resource_manager/cloud_formation_templates/GatewayLoadBalancerTemplate.yml | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>PrivateSubnetWithNATGateway}} | {{cfn-output:VPC>VPCCidr}} |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml         | SHARED       |                          |                                                    |                            |
    When alarm "elb:alarm:gateway_unhealthy_host_count:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | GatewayLoadBalancerName                                       | TargetGroup                                            | Threshold | EvaluationPeriods | DatapointsToAlarm |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:GatewayLoadBalancerTemplate>GatewayELBFullName}} | {{cfn-output:GatewayLoadBalancerTemplate>TargetGroup}} | 1         | 1                 | 1                 |
    And set target group "{{cfn-output:GatewayLoadBalancerTemplate>TargetGroupArn}}" healthcheck port "65534"
    Then assert metrics for all alarms are populated
    Then wait until alarm {{alarm:under_test>AlarmName}} becomes ALARM within 180 seconds, check every 15 seconds


