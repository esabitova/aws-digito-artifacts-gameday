@lambda
Feature: SSM automation document to change memory size of the given Lambda Function

  Scenario: Change memory size of Lambda Function
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                               | ResourceType |
      | resource_manager/cloud_formation_templates/LambdaTemplate.yml                                 | ON_DEMAND    |
      | documents/lambda/sop/change_memory_size/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-ChangeLambdaMemorySizeSOP_2020-10-26" SSM document
    And cache value of memory size as "OldMemorySize" at the lambda "before" SSM automation execution
      | LambdaARN                               |
      | {{cfn-output:LambdaTemplate>LambdaARN}} |
    And the cached input parameters
      | NewMemorySize | BeforeMemorySize |
      | 10240         | 2000             |
    And cache constant value {{cache:NewMemorySize}} as "ExpectedMemorySize" "before" SSM automation execution
    And SSM automation document "Digito-ChangeLambdaMemorySizeSOP_2020-10-26" executed
      | LambdaARN                               | NewMemorySizeValue      | AutomationAssumeRole                                                                  |
      | {{cfn-output:LambdaTemplate>LambdaARN}} | {{cache:NewMemorySize}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoChangeLambdaMemorySizeSOPAssumeRole}} |
    When SSM automation document "Digito-ChangeLambdaMemorySizeSOP_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And wait for lambda memory size to have a new value for "120" seconds
      | LambdaARN                               | MemorySize              |
      | {{cfn-output:LambdaTemplate>LambdaARN}} | {{cache:NewMemorySize}} |
    And cache value of memory size as "ActualMemorySize" at the lambda "after" SSM automation execution
      | LambdaARN                               |
      | {{cfn-output:LambdaTemplate>LambdaARN}} |
    Then assert "OldMemorySize" at "before" became not equal to "ActualMemorySize" at "after"
    Then assert "ExpectedMemorySize" at "before" became equal to "ActualMemorySize" at "after"
    Then SSM automation document "Digito-ChangeLambdaMemorySizeSOP_2020-10-26" executed
      | LambdaARN                               | NewMemorySizeValue         | AutomationAssumeRole                                                                  |
      | {{cfn-output:LambdaTemplate>LambdaARN}} | {{cache:BeforeMemorySize}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoChangeLambdaMemorySizeSOPAssumeRole}} |
    And SSM automation document "Digito-ChangeLambdaMemorySizeSOP_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And wait for lambda memory size to have a new value for "120" seconds
      | LambdaARN                               | MemorySize                 |
      | {{cfn-output:LambdaTemplate>LambdaARN}} | {{cache:BeforeMemorySize}} |
    And cache value of memory size as "RevertedMemorySize" at the lambda "after" SSM automation execution
      | LambdaARN                               |
      | {{cfn-output:LambdaTemplate>LambdaARN}} |
    And assert "OldMemorySize" at "before" became equal to "RevertedMemorySize" at "after"
