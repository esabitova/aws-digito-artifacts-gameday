@elb
Feature: SSM automation document Digito-NetworkGwLbTargetUnavailable_2020-04-01

  Scenario: Create Network LB and execute automation to make the target group unavailable in rollback
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                           | ResourceType | VPC                      | Subnet1                                            | Subnet2                                          | EC2Subnet                                      | VPCCidr                    |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                                                 | SHARED       |                          |                                                    |                                                  |                                                |                            |
      | resource_manager/cloud_formation_templates/shared/CommonAlarms.yml                                        | SHARED       |                          |                                                    |                                                  |                                                |                            |
      | resource_manager/cloud_formation_templates/NetworkLoadBalancerTemplate.yml                                | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetOne}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetTwo}} | {{cfn-output:VPC>PrivateSubnetWithInternet01}} | {{cfn-output:VPC>VPCCidr}} |
      | documents/elb/test/network_gw_lb_target_unavailable/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                          |                                                    |                                                  |                                                |                            |
    And published "Digito-NetworkGwLbTargetUnavailable_2020-04-01" SSM document
    And cache target group HealthCheckPort as "OldPort" "before" SSM automation execution
      | LoadBalancerArn                                          |
      | {{cfn-output:NetworkLoadBalancerTemplate>NetworkELBArn}} |

    When SSM automation document "Digito-NetworkGwLbTargetUnavailable_2020-04-01" executed
      | LoadBalancerArn                                          | SyntheticAlarmName                            | AutomationAssumeRole                                                                                 |
      | {{cfn-output:NetworkLoadBalancerTemplate>NetworkELBArn}} | {{cfn-output:CommonAlarms>AlwaysOKAlarmName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoLoadBalancerNetworkGWLbTargetUnavailableAssumeRole}} |
    And Wait for the SSM automation document "Digito-NetworkGwLbTargetUnavailable_2020-04-01" execution is on step "AssertAlarmToBeRed" in status "InProgress" for "600" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache target group HealthCheckPort as "NewPort" "after" SSM automation execution
      | LoadBalancerArn                                          |
      | {{cfn-output:NetworkLoadBalancerTemplate>NetworkELBArn}} |
    And terminate "Digito-NetworkGwLbTargetUnavailable_2020-04-01" SSM automation document
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    Then Wait for the SSM automation document "Digito-NetworkGwLbTargetUnavailable_2020-04-01" execution is on step "TriggerRollback" in status "Success" for "240" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And SSM automation document "Digito-NetworkGwLbTargetUnavailable_2020-04-01" execution in status "Cancelled"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache rollback execution id
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And SSM automation document "Digito-NetworkGwLbTargetUnavailable_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>2}} |
    And cache target group HealthCheckPort as "OldPort" "after" SSM automation execution
      | LoadBalancerArn                                          |
      | {{cfn-output:NetworkLoadBalancerTemplate>NetworkELBArn}} |
    And assert "OldPort" at "before" became equal to "OldPort" at "after"
    And assert "OldPort" at "before" became not equal to "NewPort" at "after"


  Scenario: Create Gateway LB and execute automation to make the target group unavailable in rollback
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                           | ResourceType | VPC                      | Subnet                                             | EC2Subnet                                      | VPCCidr                    |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                                                 | SHARED       |                          |                                                    |                                                |                            |
      | resource_manager/cloud_formation_templates/shared/CommonAlarms.yml                                        | SHARED       |                          |                                                    |                                                |                            |
      | resource_manager/cloud_formation_templates/GatewayLoadBalancerTemplate.yml                                | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetOne}} | {{cfn-output:VPC>PrivateSubnetWithInternet01}} | {{cfn-output:VPC>VPCCidr}} |
      | documents/elb/test/network_gw_lb_target_unavailable/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                          |                                                    |                                                |                            |
    And published "Digito-NetworkGwLbTargetUnavailable_2020-04-01" SSM document
    And cache target group HealthCheckPort as "OldPort" "before" SSM automation execution
      | LoadBalancerArn                                          |
      | {{cfn-output:GatewayLoadBalancerTemplate>GatewayELBArn}} |

    When SSM automation document "Digito-NetworkGwLbTargetUnavailable_2020-04-01" executed
      | LoadBalancerArn                                          | SyntheticAlarmName                            | AutomationAssumeRole                                                                                 |
      | {{cfn-output:GatewayLoadBalancerTemplate>GatewayELBArn}} | {{cfn-output:CommonAlarms>AlwaysOKAlarmName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoLoadBalancerNetworkGWLbTargetUnavailableAssumeRole}} |
    And Wait for the SSM automation document "Digito-NetworkGwLbTargetUnavailable_2020-04-01" execution is on step "AssertAlarmToBeRed" in status "InProgress" for "600" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache target group HealthCheckPort as "NewPort" "after" SSM automation execution
      | LoadBalancerArn                                          |
      | {{cfn-output:GatewayLoadBalancerTemplate>GatewayELBArn}} |
    And terminate "Digito-NetworkGwLbTargetUnavailable_2020-04-01" SSM automation document
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    Then Wait for the SSM automation document "Digito-NetworkGwLbTargetUnavailable_2020-04-01" execution is on step "TriggerRollback" in status "Success" for "240" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And SSM automation document "Digito-NetworkGwLbTargetUnavailable_2020-04-01" execution in status "Cancelled"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache rollback execution id
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And SSM automation document "Digito-NetworkGwLbTargetUnavailable_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>2}} |
    And cache target group HealthCheckPort as "OldPort" "after" SSM automation execution
      | LoadBalancerArn                                          |
      | {{cfn-output:GatewayLoadBalancerTemplate>GatewayELBArn}} |
    And assert "OldPort" at "before" became equal to "OldPort" at "after"
    And assert "OldPort" at "before" became not equal to "NewPort" at "after"
