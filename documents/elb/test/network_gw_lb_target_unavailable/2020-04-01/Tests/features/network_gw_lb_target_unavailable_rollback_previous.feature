@elb
Feature: SSM automation document Digito-NetworkGwLbTargetUnavailable_2020-04-01

  Scenario: Create Network LB and execute automation in rollback
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                                     | ResourceType |
      | resource_manager/cloud_formation_templates/NetworkLoadBalancerTemplate.yml                                          | ON_DEMAND    |
      | documents/elb/test/network_gw_lb_target_unavailable/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-NetworkGwLbTargetUnavailable_2020-04-01" SSM document
    # Add any pre-execution caching and setup steps here

    When SSM automation document "Digito-NetworkGwLbTargetUnavailable_2020-04-01" executed
      # Add other parameter names below
      | LoadBalancerArn                                            | AutomationAssumeRole                                                                               | SyntheticAlarmName                               |
      # Replace parameter values to point to the corresponding outputs in cloudformation template
      | {{cfn-output:NetworkLoadBalancerTemplate>LoadBalancerArn}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoLoadBalancerNetworkLbTargetUnavailableAssumeRole}} | {{cfn-output:NetworkLoadBalancerTemplate>Alarm}} |
    # Add other steps that should parallel to the document here
    And Wait for the SSM automation document "Digito-NetworkGwLbTargetUnavailable_2020-04-01" execution is on step "AssertAlarmToBeRed" in status "InProgress" for "600" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
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
  # Add any post-execution caching and validation here


  Scenario: Create Gateway LB and execute automation in rollback
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                                     | ResourceType |
      | resource_manager/cloud_formation_templates/GatewayLoadBalancerTemplate.yml                                          | ON_DEMAND    |
      | documents/elb/test/network_gw_lb_target_unavailable/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-NetworkGwLbTargetUnavailable_2020-04-01" SSM document
    # Add any pre-execution caching and setup steps here

    When SSM automation document "Digito-NetworkGwLbTargetUnavailable_2020-04-01" executed
      # Add other parameter names below
      | LoadBalancerArn                                            | AutomationAssumeRole                                                                               | SyntheticAlarmName                               |
      # Replace parameter values to point to the corresponding outputs in cloudformation template
      | {{cfn-output:GatewayLoadBalancerTemplate>LoadBalancerArn}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoLoadBalancerNetworkLbTargetUnavailableAssumeRole}} | {{cfn-output:NetworkLoadBalancerTemplate>Alarm}} |
    # Add other steps that should parallel to the document here
    And Wait for the SSM automation document "Digito-NetworkGwLbTargetUnavailable_2020-04-01" execution is on step "AssertAlarmToBeRed" in status "InProgress" for "600" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
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
# Add any post-execution caching and validation here
