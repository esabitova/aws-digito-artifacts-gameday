@elb
Feature: SSM automation document Digito-NetworkGwLbTargetUnavailable_2020-04-01

  Scenario: Create Network LB and execute automation to make the target group unavailable to test failure case
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                           | ResourceType |
      | resource_manager/cloud_formation_templates/NetworkLoadBalancerTemplate.yml                                | ON_DEMAND    |
      | documents/elb/test/network_gw_lb_target_unavailable/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-NetworkGwLbTargetUnavailable_2020-04-01" SSM document
    # Add any pre-execution caching and setup steps here

    When SSM automation document "Digito-NetworkGwLbTargetUnavailable_2020-04-01" executed
      # Add other parameter names below
      | LoadBalancerArn                                            | AutomationAssumeRole                                                                               | SyntheticAlarmName                                       |
      # Replace parameter values to point to the corresponding outputs in cloudformation template
      | {{cfn-output:NetworkLoadBalancerTemplate>LoadBalancerArn}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoLoadBalancerNetworkLbTargetUnavailableAssumeRole}} | {{cfn-output:NetworkLoadBalancerTemplate>AlwaysOKAlarm}} |
    # Add other steps that should parallel to the document here
    And Wait for the SSM automation document "${documentName}" execution is on step "AssertAlarmToBeRed" in status "TimedOut" for "1000" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    # Add any step required to rectify the alarm here

    Then Wait for the SSM automation document "Digito-NetworkGwLbTargetUnavailable_2020-04-01" execution is on step "AssertAlarmToBeGreen " in status "Success" for "1000" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And SSM automation document "Digito-NetworkGwLbTargetUnavailable_2020-04-01" execution in status "TimedOut"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
  # Add any post-execution caching and validation here


  Scenario: Create Gateway LB and execute automation to make the target group unavailable to test failure case
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                                     | ResourceType |
      | resource_manager/cloud_formation_templates/GatewayLoadBalancerTemplate.yml                                          | ON_DEMAND    |
      | documents/elb/test/network_gw_lb_target_unavailable/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-NetworkGwLbTargetUnavailable_2020-04-01" SSM document
    # Add any pre-execution caching and setup steps here

    When SSM automation document "Digito-NetworkGwLbTargetUnavailable_2020-04-01" executed
      # Add other parameter names below
      | LoadBalancerArn                                            | AutomationAssumeRole                                                                               | SyntheticAlarmName                                       |
      # Replace parameter values to point to the corresponding outputs in cloudformation template
      | {{cfn-output:GatewayLoadBalancerTemplate>LoadBalancerArn}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoLoadBalancerNetworkLbTargetUnavailableAssumeRole}} | {{cfn-output:NetworkLoadBalancerTemplate>AlwaysOKAlarm}} |
    # Add other steps that should parallel to the document here
    And Wait for the SSM automation document "${documentName}" execution is on step "AssertAlarmToBeRed" in status "TimedOut" for "1000" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    # Add any step required to rectify the alarm here

    Then Wait for the SSM automation document "Digito-NetworkGwLbTargetUnavailable_2020-04-01" execution is on step "AssertAlarmToBeGreen " in status "Success" for "1000" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And SSM automation document "Digito-NetworkGwLbTargetUnavailable_2020-04-01" execution in status "TimedOut"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
# Add any post-execution caching and validation here
