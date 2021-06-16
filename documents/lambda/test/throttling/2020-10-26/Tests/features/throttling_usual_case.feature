@lambda
Feature: SSM automation document throttling

  Scenario: Execute SSM automation document throttling
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                        | ResourceType |
      | resource_manager/cloud_formation_templates/LambdaTemplate.yml                          | ON_DEMAND    |
      | documents/lambda/test/throttling/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-Throttling_2020-10-26" SSM document

    When SSM automation document "Digito-Throttling_2020-10-26" executed
      | LambdaARN                               | AutomationAssumeRole                                                         | ThrottlesAlarmName                           |
      | {{cfn-output:LambdaTemplate>LambdaARN}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoLambdaThrottlingAssumeRole}} | {{cfn-output:LambdaTemplate>ThrottlesAlarm}} |

    And Wait for the SSM automation document "Digito-Throttling_2020-10-26" execution is on step "EnableFunctionThrottling" in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And invoke throttled function
      | LambdaARN                               |
      | {{cfn-output:LambdaTemplate>LambdaARN}} |

    Then SSM automation document "Digito-Throttling_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |