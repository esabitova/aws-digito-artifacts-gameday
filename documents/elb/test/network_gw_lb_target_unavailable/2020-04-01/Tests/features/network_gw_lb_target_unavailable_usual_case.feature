@elb
Feature: SSM automation document Digito-NetworkGwLbTargetUnavailable_2020-04-01

  Scenario: Create Network LB and execute automation
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                           | ResourceType |  VPC                     | PrivateSubnet                                     | VPCCidr                     |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                                                 | SHARED       |                          |                                                   |                             |
      | resource_manager/cloud_formation_templates/NetworkLoadBalancerTemplate.yml                                | ON_DEMAND    | {{cfn-output:VPC>VPCId}} |{{cfn-output:VPC>PrivateSubnetWithoutInternetOne}} | {{cfn-output:VPC>VPCCidr}}  |
      | documents/elb/test/network_gw_lb_target_unavailable/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                          |                                                   |                             |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml                                        | SHARED       |                          |                                                   |                             |
    And published "Digito-NetworkGwLbTargetUnavailable_2020-04-01" SSM document
    And alarm "elb:alarm:network_unhealthy_host_count:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | NetworkELBName                                                | TargetGroup                                            | Threshold  |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:NetworkLoadBalancerTemplate>NetworkELBFullName}} | {{cfn-output:NetworkLoadBalancerTemplate>TargetGroup}} | 1          |
    When SSM automation document "Digito-NetworkGwLbTargetUnavailable_2020-04-01" executed
      | LoadBalancerArn                                          | SyntheticAlarmName             |  AutomationAssumeRole                                                                                |
      | {{cfn-output:NetworkLoadBalancerTemplate>NetworkELBArn}} | {{alarm:under_test>AlarmName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoLoadBalancerNetworkGWLbTargetUnavailableAssumeRole}} |

    Then SSM automation document "Digito-NetworkGwLbTargetUnavailable_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |


  Scenario: Create Gateway LB and execute automation
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                           | ResourceType |  VPC                     | PrivateSubnet                                     | VPCCidr                     |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                                                 | SHARED       |                          |                                                   |                             |
      | resource_manager/cloud_formation_templates/GatewayLoadBalancerTemplate.yml                                | ON_DEMAND    | {{cfn-output:VPC>VPCId}} |{{cfn-output:VPC>PrivateSubnetWithoutInternetOne}} | {{cfn-output:VPC>VPCCidr}}  |
      | documents/elb/test/network_gw_lb_target_unavailable/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                          |                                                   |                             |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml                                        | SHARED       |                          |                                                   |                             |
    And published "Digito-NetworkGwLbTargetUnavailable_2020-04-01" SSM document
    And alarm "elb:alarm:gateway_unhealthy_host_count:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | GatewayELBFullName                                            | TargetGroup                                            | Threshold  |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:GatewayLoadBalancerTemplate>GatewayELBFullName}} | {{cfn-output:GatewayLoadBalancerTemplate>TargetGroup}} | 1          |
    When SSM automation document "Digito-NetworkGwLbTargetUnavailable_2020-04-01" executed
      | LoadBalancerArn                                          | SyntheticAlarmName             |  AutomationAssumeRole                                                                              |
      | {{cfn-output:GatewayLoadBalancerTemplate>GatewayELBArn}} | {{alarm:under_test>AlarmName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoLoadBalancerNetworkGWLbTargetUnavailableAssumeRole}} |

    Then SSM automation document "Digito-NetworkGwLbTargetUnavailable_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |