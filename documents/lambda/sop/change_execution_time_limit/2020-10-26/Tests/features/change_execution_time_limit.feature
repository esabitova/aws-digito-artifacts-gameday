@lambda
Feature: SSM automation document for changing execution time limit of Lambda.

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document for changing execution time limit of Lambda
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                        | ResourceType |
      | resource_manager/cloud_formation_templates/LambdaTemplate.yml                                          | ON_DEMAND    |
      | documents/lambda/sop/change_execution_time_limit/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-ChangeLambdaExecutionTimeLimitSOP_2020-10-26" SSM document
    And cached current execution time limit as "Timeout" at step "before"
      | LambdaARN                               |
      | {{cfn-output:LambdaTemplate>LambdaARN}} |
    And the cached input parameters
      | TimeoutValue |
      | 570          |
    And SSM automation document "Digito-ChangeLambdaExecutionTimeLimitSOP_2020-10-26" executed
      | NewTimeoutValueSeconds | LambdaARN                               | AutomationAssumeRole                                                                          |
      | {{cache:TimeoutValue}} | {{cfn-output:LambdaTemplate>LambdaARN}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoChangeLambdaExecutionTimeLimitSOPAssumeRole}} |

    When SSM automation document "Digito-ChangeLambdaExecutionTimeLimitSOP_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And sleep for "60" seconds
    Then assert execution time limit is equal to input value
      | LambdaARN                               | ExpectedValue          |
      | {{cfn-output:LambdaTemplate>LambdaARN}} | {{cache:TimeoutValue}} |

    And SSM automation document "Digito-ChangeLambdaExecutionTimeLimitSOP_2020-10-26" executed
      | NewTimeoutValueSeconds   | LambdaARN                               | AutomationAssumeRole                                                                          |
      | {{cache:before>Timeout}} | {{cfn-output:LambdaTemplate>LambdaARN}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoChangeLambdaExecutionTimeLimitSOPAssumeRole}} |
    And SSM automation document "Digito-ChangeLambdaExecutionTimeLimitSOP_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>2}} |
    And sleep for "60" seconds
    Then assert execution time limit is equal to input value
      | LambdaARN                               | ExpectedValue            |
      | {{cfn-output:LambdaTemplate>LambdaARN}} | {{cache:before>Timeout}} |