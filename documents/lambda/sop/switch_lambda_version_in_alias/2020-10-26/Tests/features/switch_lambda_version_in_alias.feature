@lambda
Feature: SSM automation document to switch version in alias of the given Lambda Function

  Scenario: Switch Alias of Lambda functions to another version
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                           | ResourceType |
      | resource_manager/cloud_formation_templates/LambdaTemplate.yml                                             | ON_DEMAND    |
      | documents/lambda/sop/switch_lambda_version_in_alias/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-LambdaSwitchLambdaVersionInAlias_2020-10-26" SSM document
    And SSM automation document "Digito-LambdaSwitchLambdaVersionInAlias_2020-10-26" executed
      | LambdaARN                               | LambdaVersion | AliasName | AutomationAssumeRole                                                                            |
      | {{cfn-output:LambdaTemplate>LambdaARN}} | $LATEST       | actual    | {{cfn-output:AutomationAssumeRoleTemplate>DigitoLambdaSwitchLambdaVersionInAliasAssumeRoleArn}} |
    When SSM automation document "Digito-LambdaSwitchLambdaVersionInAlias_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
