# @elb
Feature: SSM automation document Digito-ApplicationLbNetworkUnavailable_2020-04-01

  Scenario: Execute SSM automation document Digito-ApplicationLbNetworkUnavailable_2020-04-01 to test failure case
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath     | ResourceType |
      | resource_manager/cloud_formation_templates/ApplicationLoadBalancerTemplate.yml  | ON_DEMAND    |
      | documents/elb/test/application_lb_network_unavailable/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-ApplicationLbNetworkUnavailable_2020-04-01" SSM document
    # Add any pre-execution caching and setup steps here

    When SSM automation document "Digito-ApplicationLbNetworkUnavailable_2020-04-01" executed
    # Add other parameter names below
      | LoadBalancerArn                                       | AutomationAssumeRole                                                              | SyntheticAlarmName                                                |
    # Replace parameter values to point to the corresponding outputs in cloudformation template
      | {{cfn-output:ApplicationLoadBalancerTemplate>LoadBalancerArn}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoLoadBalancerApplicationLbNetworkUnavailableAssumeRole}} | {{cfn-output:ApplicationLoadBalancerTemplate>AlwaysOKAlarm}} |
    # Add other steps that should parallel to the document here
    And Wait for the SSM automation document "${documentName}" execution is on step "AssertAlarmToBeRed" in status "TimedOut" for "1000" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    # Add any step required to rectify the alarm here

    Then Wait for the SSM automation document "Digito-ApplicationLbNetworkUnavailable_2020-04-01" execution is on step "AssertAlarmToBeGreen " in status "Success" for "1000" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And SSM automation document "Digito-ApplicationLbNetworkUnavailable_2020-04-01" execution in status "TimedOut"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    # Add any post-execution caching and validation here
