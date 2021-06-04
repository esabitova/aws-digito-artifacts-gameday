@lambda
Feature: SSM automation document Digito-LambdaBreakSecurityGroup_2020-09-21

  Scenario: Execute SSM automation document Digito-LambdaBreakSecurityGroup_2020-09-21 to test failure case
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath     | ResourceType |
      | resource_manager/cloud_formation_templates/LambdaTemplate.yml  | ON_DEMAND    |
      | documents/lambda/test/break_security_group/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-LambdaBreakSecurityGroup_2020-09-21" SSM document
    And cache security group list for a lambda as "SecurityGroupList" "before" SSM automation execution
      | LambdaARN                               |
      | {{cfn-output:LambdaTemplate>LambdaARN}} |
    When SSM automation document "Digito-LambdaBreakSecurityGroup_2020-09-21" executed
      | LambdaARN                               |  LambdaErrorAlarmName                                     | AutomationAssumeRole                                                                  |
      | {{cfn-output:LambdaTemplate>LambdaARN}} |  {{cfn-output:LambdaTemplate>ConcurrentExecutionsAlarm}}  | {{cfn-output:AutomationAssumeRoleTemplate>DigitoLambdaBreakSecurityGroupAssumeRole}}  |
    And Wait for the SSM automation document "Digito-LambdaBreakSecurityGroup_2020-09-21" execution is on step "AssertAlarmToBeRed" in status "TimedOut" for "1000" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    Then Wait for the SSM automation document "Digito-LambdaBreakSecurityGroup_2020-09-21" execution is on step "AssertAlarmToBeGreen" in status "Success" for "1000" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And SSM automation document "Digito-LambdaBreakSecurityGroup_2020-09-21" execution in status "TimedOut"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    And cache security group list for a lambda as "SecurityGroupList" "after" SSM automation execution
      | LambdaARN                               |
      | {{cfn-output:LambdaTemplate>LambdaARN}} |
    And assert "SecurityGroupList" at "before" became equal to "SecurityGroupList" at "after"