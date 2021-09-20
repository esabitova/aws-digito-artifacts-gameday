@lambda
Feature: SSM automation document to switch version in alias of the given Lambda Function

  Scenario: Switch Alias of Lambda functions to another version
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                           | ResourceType |
      | resource_manager/cloud_formation_templates/LambdaTemplate.yml                                             | ON_DEMAND    |
      | documents/lambda/sop/switch_lambda_version_in_alias/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
      | documents/lambda/sop/change_memory_size/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml             | ASSUME_ROLE  |
    And published "Digito-SwitchLambdaVersionInAliasSOP_2020-10-26" SSM document
    And published "Digito-ChangeLambdaMemorySizeSOP_2020-10-26" SSM document
    And the cached input parameters
      | NewMemorySize | BeforeMemorySize |
      | 4000          | 2000             |
    And create alias and cache its name as "AliasName" at step "before"
      | LambdaARN                               | LambdaVersion                               |
      | {{cfn-output:LambdaTemplate>LambdaARN}} | {{cfn-output:LambdaTemplate>LambdaVersion}} |
    And SSM automation document "Digito-ChangeLambdaMemorySizeSOP_2020-10-26" executed
      | LambdaARN                               | NewMemorySizeValue      | AutomationAssumeRole                                                                  |
      | {{cfn-output:LambdaTemplate>LambdaARN}} | {{cache:NewMemorySize}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoChangeLambdaMemorySizeSOPAssumeRole}} |
    And SSM automation document "Digito-ChangeLambdaMemorySizeSOP_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And wait for lambda memory size to have a new value for "120" seconds
      | LambdaARN                               | MemorySize              |
      | {{cfn-output:LambdaTemplate>LambdaARN}} | {{cache:NewMemorySize}} |
    And published function version and cached version as "NewFunctionVersion" at step "before"
      | LambdaARN                               |
      | {{cfn-output:LambdaTemplate>LambdaARN}} |

    And SSM automation document "Digito-SwitchLambdaVersionInAliasSOP_2020-10-26" executed
      | LambdaARN                               | LambdaVersion                       | AliasName                  | AutomationAssumeRole                                                                      |
      | {{cfn-output:LambdaTemplate>LambdaARN}} | {{cache:before>NewFunctionVersion}} | {{cache:before>AliasName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoSwitchLambdaVersionInAliasSOPAssumeRole}} |
    And SSM automation document "Digito-SwitchLambdaVersionInAliasSOP_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>2}} |
    Then assert version in alias changed
      | LambdaARN                               | LambdaVersion                       | AliasName                  |
      | {{cfn-output:LambdaTemplate>LambdaARN}} | {{cache:before>NewFunctionVersion}} | {{cache:before>AliasName}} |

# revert memory size and remove alias and version
    And SSM automation document "Digito-ChangeLambdaMemorySizeSOP_2020-10-26" executed
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
    And delete alias
      | LambdaARN                               | AliasName                  |
      | {{cfn-output:LambdaTemplate>LambdaARN}} | {{cache:before>AliasName}} |
    And delete function version
      | LambdaARN                               | LambdaVersion                       |
      | {{cfn-output:LambdaTemplate>LambdaARN}} | {{cache:before>NewFunctionVersion}} |
