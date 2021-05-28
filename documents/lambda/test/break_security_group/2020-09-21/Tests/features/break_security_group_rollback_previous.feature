@lambda
Feature: SSM automation document Digito-LambdaBreakSecurityGroup_2020-09-21

  Scenario: Execute SSM automation document Digito-LambdaBreakSecurityGroup_2020-09-21 in rollback
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath     | ResourceType |
      | resource_manager/cloud_formation_templates/LambdaTemplate.yml  | ON_DEMAND    |
      | documents/lambda/test/break_security_group/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-LambdaBreakSecurityGroup_2020-09-21" SSM document
    # Add any pre-execution caching and setup steps here

    When SSM automation document "Digito-LambdaBreakSecurityGroup_2020-09-21" executed
    # Add other parameter names below
      | LambdaARN                                   | AutomationAssumeRole                                                           | SyntheticAlarmName                                 |
    # Replace parameter values to point to the corresponding outputs in cloudformation template
      | {{cfn-output:LambdaTemplate>LambdaArn}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoLambdaBreakSecurityGroupAssumeRole}} | {{cfn-output:LambdaTemplate>ErrorsAlarm}} |
    # Add other steps that should parallel to the document here
    And Wait for the SSM automation document "Digito-LambdaBreakSecurityGroup_2020-09-21" execution is on step "AssertAlarmToBeRed" in status "InProgress" for "600" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And terminate "Digito-LambdaBreakSecurityGroup_2020-09-21" SSM automation document
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    Then Wait for the SSM automation document "Digito-LambdaBreakSecurityGroup_2020-09-21" execution is on step "TriggerRollback" in status "Success" for "240" seconds
      | ExecutionId               |
      | {{cache:SsmExecutionId>1}}|
    And SSM automation document "Digito-LambdaBreakSecurityGroup_2020-09-21" execution in status "Cancelled"
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|
    And cache rollback execution id
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|
    And SSM automation document "Digito-LambdaBreakSecurityGroup_2020-09-21" execution in status "Success"
      |ExecutionId               |
      |{{cache:SsmExecutionId>2}}|
    # Add any post-execution caching and validation here
