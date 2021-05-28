@lambda
Feature: SSM automation document Digito-LambdaBreakSecurityGroup_2020-09-21

  Scenario: Execute SSM automation document Digito-LambdaBreakSecurityGroup_2020-09-21
    Given cache lambda code for accessing s3 bucket as "LambdaCode" "before" SSM automation execution
    And the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                   | ResourceType | LambdaCode                   |
      | resource_manager/cloud_formation_templates/LambdaTemplate.yml                                     | ON_DEMAND    | {{cache:before>LambdaCode}}  |
      | documents/lambda/test/break_security_group/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml  | ASSUME_ROLE  |                              |
    And published "Digito-LambdaBreakSecurityGroup_2020-09-21" SSM document

    When SSM automation document "Digito-LambdaBreakSecurityGroup_2020-09-21" executed
      | LambdaARN                               |  LambdaErrorAlarmName                      | AutomationAssumeRole                                                                  |
      | {{cfn-output:LambdaTemplate>LambdaARN}} |  {{cfn-output:LambdaTemplate>ErrorsAlarm}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoLambdaBreakSecurityGroupAssumeRole}}  |

    Then SSM automation document "Digito-LambdaBreakSecurityGroup_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
