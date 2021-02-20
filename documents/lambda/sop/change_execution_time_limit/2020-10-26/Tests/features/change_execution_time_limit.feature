@lambda
Feature: SSM automation document for changing execution time limit of Lambda.

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document for changing execution time limit of Lambda
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                         | ResourceType |
      | resource_manager/cloud_formation_templates/LambdaTemplate.yml                                           | ON_DEMAND    |
      | documents/lambda/sop/change_execution_time_limit/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And cache value of "Timeout" as "OldTimeout" "before" SSM automation execution
      | LambdaArn                               |
      | {{cfn-output:LambdaTemplate>LambdaARN}} |
    And generate different value of "Timeout" than "OldTimeout" as "ExpectedTimeout" "before" SSM automation execution
      | OldTimeout                  |
      | {{cache:before>OldTimeout}} |
    And SSM automation document "Digito-ChangeExecutionTimeLimit_2020-10-26" executed
      | NewTimeoutValueSeconds                       | LambdaARN                               | AutomationAssumeRole                                                                 |
      | {{cache:before>ExpectedTimeout}} | {{cfn-output:LambdaTemplate>LambdaARN}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoChangeExecutionTimeLimitAssumeRole}} |

    When SSM automation document "Digito-ChangeExecutionTimeLimit_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache value of "Timeout" as "ActualTimeout" "after" SSM automation execution
      | LambdaArn                               |
      | {{cfn-output:LambdaTemplate>LambdaARN}} |

    Then assert "ExpectedTimeout" at "before" became equal to "ActualTimeout" at "after"
    And assert "OldTimeout" at "before" became not equal to "ActualTimeout" at "after"