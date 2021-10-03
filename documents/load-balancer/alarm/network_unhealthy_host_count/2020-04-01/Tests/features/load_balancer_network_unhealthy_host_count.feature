@load-balancer @integration @alarm
Feature: Alarm Setup - load-balancer UnHealthyHostCount

  Scenario: Create load-balancer:alarm:network_unhealthy_host_count:2020-04-01 based on UnHealthyHostCount metric and check OK status
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                            | ResourceType | VPC                      | Subnet1                                            | Subnet2                                            | EC2Subnet                                      | VPCCidr                    |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                  | SHARED       |                          |                                                    |                                                    |                                                |                            |
      | resource_manager/cloud_formation_templates/NetworkLoadBalancerTemplate.yml | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetOne}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetTwo}} | {{cfn-output:VPC>PrivateSubnetWithInternet01}} | {{cfn-output:VPC>VPCCidr}} |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml         | SHARED       |                          |                                                    |                                                    |                                                |                            |
    When alarm "load-balancer:alarm:network_unhealthy_host_count:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | NetworkLoadBalancerName                                       | TargetGroup                                            | Threshold | EvaluationPeriods | DatapointsToAlarm |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:NetworkLoadBalancerTemplate>NetworkELBFullName}} | {{cfn-output:NetworkLoadBalancerTemplate>TargetGroup}} | 1000      | 1                 | 1                 |
    And set target group "{{cfn-output:NetworkLoadBalancerTemplate>TargetGroupArn}}" healthcheck port "65534"
    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 180 seconds, check every 15 seconds

  Scenario: Create load-balancer:alarm:network_unhealthy_host_count:2020-04-01 based on UnHealthyHostCount metric and check ALARM status
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                            | ResourceType | VPC                      | Subnet1                                            | Subnet2                                            | EC2Subnet                                      | VPCCidr                    |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                  | SHARED       |                          |                                                    |                                                    |                                                |                            |
      | resource_manager/cloud_formation_templates/NetworkLoadBalancerTemplate.yml | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetOne}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetTwo}} | {{cfn-output:VPC>PrivateSubnetWithInternet01}} | {{cfn-output:VPC>VPCCidr}} |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml         | SHARED       |                          |                                                    |                                                    |                                                |                            |
    When alarm "load-balancer:alarm:network_unhealthy_host_count:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | NetworkLoadBalancerName                                       | TargetGroup                                            | Threshold | EvaluationPeriods | DatapointsToAlarm |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:NetworkLoadBalancerTemplate>NetworkELBFullName}} | {{cfn-output:NetworkLoadBalancerTemplate>TargetGroup}} | 1         | 1                 | 1                 |
    And set target group "{{cfn-output:NetworkLoadBalancerTemplate>TargetGroupArn}}" healthcheck port "65534"
    And sleep for "60" seconds
    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes ALARM within 300 seconds, check every 15 seconds
