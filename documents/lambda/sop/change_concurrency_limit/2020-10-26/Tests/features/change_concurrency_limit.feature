@lambda
Feature: SSM automation document to change Concurrency limit of the given Lambda Function

  Scenario: Change Concurrency limit of Lambda Function
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                     | ResourceType |
      | resource_manager/cloud_formation_templates/LambdaTemplate.yml                                       | ON_DEMAND    |
      | documents/lambda/sop/change_concurrency_limit/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-ChangeLambdaConcurrencyLimitSOP_2020-10-26" SSM document
    And the cached input parameters
      | NewReservedConcurrentExecutions |
      | 50                              |
    And SSM automation document "Digito-ChangeLambdaConcurrencyLimitSOP_2020-10-26" executed
      | LambdaARN                               | AutomationAssumeRole                                                                        | NewReservedConcurrentExecutions           |
      | {{cfn-output:LambdaTemplate>LambdaARN}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoChangeLambdaConcurrencyLimitSOPAssumeRole}} | {{cache:NewReservedConcurrentExecutions}} |
    When SSM automation document "Digito-ChangeLambdaConcurrencyLimitSOP_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    Then assert current concurrent executions value is equal to input value
      | LambdaARN                               | InputValue                                |
      | {{cfn-output:LambdaTemplate>LambdaARN}} | {{cache:NewReservedConcurrentExecutions}} |
    Then delete function concurrency
      | LambdaARN                               |
      | {{cfn-output:LambdaTemplate>LambdaARN}} |


  Scenario: Set Concurrency limit out of account limits
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                     | ResourceType |
      | resource_manager/cloud_formation_templates/LambdaTemplate.yml                                       | ON_DEMAND    |
      | documents/lambda/sop/change_concurrency_limit/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-ChangeLambdaConcurrencyLimitSOP_2020-10-26" SSM document
    And the cached input parameters
      | NewReservedConcurrentExecutions |
      | 5000                            |
    And SSM automation document "Digito-ChangeLambdaConcurrencyLimitSOP_2020-10-26" executed
      | LambdaARN                               | AutomationAssumeRole                                                                        | NewReservedConcurrentExecutions           |
      | {{cfn-output:LambdaTemplate>LambdaARN}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoChangeLambdaConcurrencyLimitSOPAssumeRole}} | {{cache:NewReservedConcurrentExecutions}} |
    When SSM automation document "Digito-ChangeLambdaConcurrencyLimitSOP_2020-10-26" execution in status "Failed"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
