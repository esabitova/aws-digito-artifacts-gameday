@lambda
Feature: SSM automation document to change provisioned concurrency of the given Lambda Function

  Scenario: Change provisioned concurrency of Lambda Function by version
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                           | ResourceType |
      | resource_manager/cloud_formation_templates/LambdaTemplate.yml                                             | ON_DEMAND    |
      | documents/lambda/sop/change_provisioned_concurrency/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-ChangeLambdaProvisionedConcurrencySOP_2020-10-26" SSM document
    And the cached input parameters
      | ProvisionedConcurrentExecutions |
      | 10                              |
    And SSM automation document "Digito-ChangeLambdaProvisionedConcurrencySOP_2020-10-26" executed
      | LambdaARN                               | LambdaQualifier                             | ProvisionedConcurrentExecutions           | AutomationAssumeRole                                                                              |
      | {{cfn-output:LambdaTemplate>LambdaARN}} | {{cfn-output:LambdaTemplate>LambdaVersion}} | {{cache:ProvisionedConcurrentExecutions}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoChangeLambdaProvisionedConcurrencySOPAssumeRole}} |
    When SSM automation document "Digito-ChangeLambdaProvisionedConcurrencySOP_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    Then assert current provisioned concurrency is equal to input value
      | LambdaARN                               | InputValue                                | LambdaQualifier                             |
      | {{cfn-output:LambdaTemplate>LambdaARN}} | {{cache:ProvisionedConcurrentExecutions}} | {{cfn-output:LambdaTemplate>LambdaVersion}} |
    Then delete provisioned concurrency config
      | LambdaARN                               | LambdaQualifier                             |
      | {{cfn-output:LambdaTemplate>LambdaARN}} | {{cfn-output:LambdaTemplate>LambdaVersion}} |
    Then wait for lambda to be in active state for "300" seconds
      | LambdaARN                               |
      | {{cfn-output:LambdaTemplate>LambdaARN}} |

  Scenario: Change provisioned concurrency of Lambda Function by alias
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                           | ResourceType |
      | resource_manager/cloud_formation_templates/LambdaTemplate.yml                                             | ON_DEMAND    |
      | documents/lambda/sop/change_provisioned_concurrency/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-ChangeLambdaProvisionedConcurrencySOP_2020-10-26" SSM document
    And create alias and cache its name as "AliasName" at step "before"
      | LambdaARN                               | LambdaVersion                               |
      | {{cfn-output:LambdaTemplate>LambdaARN}} | {{cfn-output:LambdaTemplate>LambdaVersion}} |
    And the cached input parameters
      | ProvisionedConcurrentExecutions |
      | 10                              |
    And SSM automation document "Digito-ChangeLambdaProvisionedConcurrencySOP_2020-10-26" executed
      | LambdaARN                               | LambdaQualifier            | ProvisionedConcurrentExecutions           | AutomationAssumeRole                                                                              |
      | {{cfn-output:LambdaTemplate>LambdaARN}} | {{cache:before>AliasName}} | {{cache:ProvisionedConcurrentExecutions}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoChangeLambdaProvisionedConcurrencySOPAssumeRole}} |
    When SSM automation document "Digito-ChangeLambdaProvisionedConcurrencySOP_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    Then assert current provisioned concurrency is equal to input value
      | LambdaARN                               | InputValue                                | LambdaQualifier            |
      | {{cfn-output:LambdaTemplate>LambdaARN}} | {{cache:ProvisionedConcurrentExecutions}} | {{cache:before>AliasName}} |
    Then delete provisioned concurrency config
      | LambdaARN                               | LambdaQualifier            |
      | {{cfn-output:LambdaTemplate>LambdaARN}} | {{cache:before>AliasName}} |
    Then wait for lambda to be in active state for "300" seconds
      | LambdaARN                               |
      | {{cfn-output:LambdaTemplate>LambdaARN}} |
    And delete alias
      | LambdaARN                               | AliasName                  |
      | {{cfn-output:LambdaTemplate>LambdaARN}} | {{cache:before>AliasName}} |