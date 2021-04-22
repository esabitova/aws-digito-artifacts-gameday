@lambda
Feature: SSM automation document to change provisioned concurrency of the given Lambda Function

  Scenario: Change provisioned concurrency of Lambda Function by version
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                           | ResourceType |
      | resource_manager/cloud_formation_templates/LambdaTemplate.yml                                             | ON_DEMAND    |
      | documents/lambda/sop/change_provisioned_concurrency/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-ChangeProvisionedConcurrency_2020-10-26" SSM document
    And the cached input parameters
      | ProvisionedConcurrentExecutions |
      | 10                              |
    And SSM automation document "Digito-ChangeProvisionedConcurrency_2020-10-26" executed
      | LambdaARN                               | LambdaQualifier                             | ProvisionedConcurrentExecutions           | AutomationAssumeRole                                                                              |
      | {{cfn-output:LambdaTemplate>LambdaARN}} | {{cfn-output:LambdaTemplate>LambdaVersion}} | {{cache:ProvisionedConcurrentExecutions}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoLambdaChangeProvisionedConcurrencyAssumeRoleArn}} |
    When SSM automation document "Digito-ChangeProvisionedConcurrency_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    Then assert current provisioned concurrency is equal to input value
      | LambdaARN                               | InputValue                                | LambdaQualifier                             |
      | {{cfn-output:LambdaTemplate>LambdaARN}} | {{cache:ProvisionedConcurrentExecutions}} | {{cfn-output:LambdaTemplate>LambdaVersion}} |
    Then delete provisioned concurrency config
      | LambdaARN                               | LambdaQualifier                             |
      | {{cfn-output:LambdaTemplate>LambdaARN}} | {{cfn-output:LambdaTemplate>LambdaVersion}} |

  Scenario: Change provisioned concurrency of Lambda Function by alias
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                           | ResourceType |
      | resource_manager/cloud_formation_templates/LambdaTemplate.yml                                             | ON_DEMAND    |
      | documents/lambda/sop/change_provisioned_concurrency/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-ChangeProvisionedConcurrency_2020-10-26" SSM document
    And the cached input parameters
      | ProvisionedConcurrentExecutions | LambdaAlias |
      | 10                              | actual      |
    And SSM automation document "Digito-ChangeProvisionedConcurrency_2020-10-26" executed
      | LambdaARN                               | LambdaQualifier       | ProvisionedConcurrentExecutions           | AutomationAssumeRole                                                                              |
      | {{cfn-output:LambdaTemplate>LambdaARN}} | {{cache:LambdaAlias}} | {{cache:ProvisionedConcurrentExecutions}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoLambdaChangeProvisionedConcurrencyAssumeRoleArn}} |
    When SSM automation document "Digito-ChangeProvisionedConcurrency_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    Then assert current provisioned concurrency is equal to input value
      | LambdaARN                               | InputValue                                | LambdaQualifier       |
      | {{cfn-output:LambdaTemplate>LambdaARN}} | {{cache:ProvisionedConcurrentExecutions}} | {{cache:LambdaAlias}} |
    Then delete provisioned concurrency config
      | LambdaARN                               | LambdaQualifier       |
      | {{cfn-output:LambdaTemplate>LambdaARN}} | {{cache:LambdaAlias}} |