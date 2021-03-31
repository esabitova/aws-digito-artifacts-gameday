#commented the test with issues
#@lambda
Feature: SSM automation document for changing execution time limit of Lambda.

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document for changing execution time limit of Lambda
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                         | ResourceType |
      | resource_manager/cloud_formation_templates/LambdaTemplate.yml                                           | ON_DEMAND    |
      | documents/lambda/sop/change_execution_time_limit/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-ChangeExecutionTimeLimit_2020-10-26" SSM document
    And SSM automation document "Digito-ChangeExecutionTimeLimit_2020-10-26" executed
      | NewTimeoutValueSeconds                       | LambdaARN                               | AutomationAssumeRole                                                                 |
      | 570 | {{cfn-output:LambdaTemplate>LambdaARN}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoChangeExecutionTimeLimitAssumeRole}} |

    When SSM automation document "Digito-ChangeExecutionTimeLimit_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
