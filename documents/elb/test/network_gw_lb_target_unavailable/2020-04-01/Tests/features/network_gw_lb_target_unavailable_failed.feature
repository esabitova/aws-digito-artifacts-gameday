@elb
Feature: SSM automation document Digito-ForceNetworkGwLbTargetUnavailableTest_2020-04-01

  Scenario: Create Network LB and execute automation to make the target group unavailable to test failure case
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                           | ResourceType |  VPC                     | Subnet                            | VPCCidr                     |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                                                 | SHARED       |                          |                                   |                             |
      | resource_manager/cloud_formation_templates/shared/CommonAlarms.yml                                        | SHARED       |                          |                                   |                             |
      | resource_manager/cloud_formation_templates/NetworkLoadBalancerTemplate.yml                                | ON_DEMAND    | {{cfn-output:VPC>VPCId}} |{{cfn-output:VPC>PublicSubnetOne}} | {{cfn-output:VPC>VPCCidr}}  |
      | documents/elb/test/network_gw_lb_target_unavailable/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                          |                                   |                             |
    And published "Digito-ForceNetworkGwLbTargetUnavailableTest_2020-04-01" SSM document
    And cache target group HealthCheckPort as "OldPort" "before" SSM automation execution
      | LoadBalancerArn                                           |
      | {{cfn-output:NetworkLoadBalancerTemplate>NetworkELBArn}}  |

    When SSM automation document "Digito-ForceNetworkGwLbTargetUnavailableTest_2020-04-01" executed
      | LoadBalancerArn                                          | SyntheticAlarmName                            | AutomationAssumeRole                                                                              |
      | {{cfn-output:NetworkLoadBalancerTemplate>NetworkELBArn}} | {{cfn-output:CommonAlarms>AlwaysOKAlarmName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoForceNetworkGwLbTargetUnavailableTestAssumeRole}} |
    And Wait for the SSM automation document "Digito-ForceNetworkGwLbTargetUnavailableTest_2020-04-01" execution is on step "AssertAlarmToBeRed" in status "TimedOut" for "1000" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    Then Wait for the SSM automation document "Digito-ForceNetworkGwLbTargetUnavailableTest_2020-04-01" execution is on step "AssertAlarmToBeGreen" in status "Success" for "1000" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And SSM automation document "Digito-ForceNetworkGwLbTargetUnavailableTest_2020-04-01" execution in status "TimedOut"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache target group HealthCheckPort as "NewPort" "after" SSM automation execution
      | LoadBalancerArn                                           |
      | {{cfn-output:NetworkLoadBalancerTemplate>NetworkELBArn}}  |
    And assert "OldPort" at "before" became equal to "NewPort" at "after"

  Scenario: Create Gateway LB and execute automation to make the target group unavailable to test failure case
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                           | ResourceType |  VPC                     | Subnet                            | VPCCidr                     |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                                                 | SHARED       |                          |                                   |                             |
      | resource_manager/cloud_formation_templates/shared/CommonAlarms.yml                                        | SHARED       |                          |                                   |                             |
      | resource_manager/cloud_formation_templates/GatewayLoadBalancerTemplate.yml                                | ON_DEMAND    | {{cfn-output:VPC>VPCId}} |{{cfn-output:VPC>PublicSubnetOne}} | {{cfn-output:VPC>VPCCidr}}  |
      | documents/elb/test/network_gw_lb_target_unavailable/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                          |                                   |                             |
    And published "Digito-ForceNetworkGwLbTargetUnavailableTest_2020-04-01" SSM document
    And cache target group HealthCheckPort as "OldPort" "before" SSM automation execution
      | LoadBalancerArn                                           |
      | {{cfn-output:GatewayLoadBalancerTemplate>GatewayELBArn}}  |

    When SSM automation document "Digito-ForceNetworkGwLbTargetUnavailableTest_2020-04-01" executed
      | LoadBalancerArn                                          | SyntheticAlarmName                            | AutomationAssumeRole                                                                              |
      | {{cfn-output:GatewayLoadBalancerTemplate>GatewayELBArn}} | {{cfn-output:CommonAlarms>AlwaysOKAlarmName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoForceNetworkGwLbTargetUnavailableTestAssumeRole}} |
    And Wait for the SSM automation document "Digito-ForceNetworkGwLbTargetUnavailableTest_2020-04-01" execution is on step "AssertAlarmToBeRed" in status "TimedOut" for "1000" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    Then Wait for the SSM automation document "Digito-ForceNetworkGwLbTargetUnavailableTest_2020-04-01" execution is on step "AssertAlarmToBeGreen" in status "Success" for "1000" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And SSM automation document "Digito-ForceNetworkGwLbTargetUnavailableTest_2020-04-01" execution in status "TimedOut"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache target group HealthCheckPort as "NewPort" "after" SSM automation execution
      | LoadBalancerArn                                           |
      | {{cfn-output:GatewayLoadBalancerTemplate>GatewayELBArn}}  |
    And assert "OldPort" at "before" became equal to "NewPort" at "after"