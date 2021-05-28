@lambda
Feature: SSM automation document Digito-LambdaBreakSecurityGroup_2020-09-21

  Scenario: Execute SSM automation document Digito-LambdaBreakSecurityGroup_2020-09-21 to test failure case
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath     | ResourceType |
      | resource_manager/cloud_formation_templates/LambdaTemplate.yml  | ON_DEMAND    |
      | documents/lambda/test/break_security_group/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-LambdaBreakSecurityGroup_2020-09-21" SSM document
    # Add any pre-execution caching and setup steps here

    When SSM automation document "Digito-LambdaBreakSecurityGroup_2020-09-21" executed
    # Add other parameter names below
      | LambdaARN                                       | AutomationAssumeRole                                                              | SyntheticAlarmName                                                |
    # Replace parameter values to point to the corresponding outputs in cloudformation template
      | {{cfn-output:LambdaTemplate>LambdaArn}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoLambdaBreakSecurityGroupAssumeRole}} | {{cfn-output:LambdaTemplate>AlwaysOKAlarm}} |
    # Add other steps that should parallel to the document here
    And Wait for the SSM automation document "${documentName" execution is on step "AssertAlarmToBeRed" in status "TimedOut" for "1000" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    # Add any step required to rectify the alarm here

    Then Wait for the SSM automation document "Digito-LambdaBreakSecurityGroup_2020-09-21" execution is on step "AssertAlarmToBeGreen" in status "Success" for "1000" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And SSM automation document "Digito-LambdaBreakSecurityGroup_2020-09-21" execution in status "TimedOut"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    # Add any post-execution caching and validation here
