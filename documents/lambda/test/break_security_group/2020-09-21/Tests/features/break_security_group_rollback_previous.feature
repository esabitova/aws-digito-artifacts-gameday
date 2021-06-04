@lambda
Feature: SSM automation document Digito-LambdaBreakSecurityGroup_2020-09-21

  Scenario: Execute SSM automation document Digito-LambdaBreakSecurityGroup_2020-09-21 in rollback
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath     | ResourceType |
      | resource_manager/cloud_formation_templates/LambdaTemplate.yml  | ON_DEMAND    |
      | documents/lambda/test/break_security_group/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-LambdaBreakSecurityGroup_2020-09-21" SSM document
    And cache security group list for a lambda as "SecurityGroupList" "before" SSM automation execution
      | LambdaARN                               |
      | {{cfn-output:LambdaTemplate>LambdaARN}} |

    When SSM automation document "Digito-LambdaBreakSecurityGroup_2020-09-21" executed
      | LambdaARN                               |  LambdaErrorAlarmName                      | AutomationAssumeRole                                                                  |
      | {{cfn-output:LambdaTemplate>LambdaARN}} |  {{cfn-output:LambdaTemplate>ErrorsAlarm}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoLambdaBreakSecurityGroupAssumeRole}}  |
    And Wait for the SSM automation document "Digito-LambdaBreakSecurityGroup_2020-09-21" execution is on step "AssertAlarmToBeRed" in status "InProgress" for "600" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache security group list for a lambda as "SecurityGroupList" "after" SSM automation execution
      | LambdaARN                               |
      | {{cfn-output:LambdaTemplate>LambdaARN}} |
    And terminate "Digito-LambdaBreakSecurityGroup_2020-09-21" SSM automation document
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    Then assert "SecurityGroupList" at "before" became not equal to "SecurityGroupList" at "after"
    And Wait for the SSM automation document "Digito-LambdaBreakSecurityGroup_2020-09-21" execution is on step "TriggerRollback" in status "Success" for "240" seconds
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
    And cache security group list for a lambda as "SecurityGroupList" "after" SSM automation execution
      | LambdaARN                               |
      | {{cfn-output:LambdaTemplate>LambdaARN}} |
    And assert "SecurityGroupList" at "before" became equal to "SecurityGroupList" at "after"