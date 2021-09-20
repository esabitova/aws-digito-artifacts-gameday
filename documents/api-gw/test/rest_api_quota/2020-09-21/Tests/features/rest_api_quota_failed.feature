@api-gw
Feature: SSM automation document Digito-ExceedRestApiGwQuotaTest_2020-09-21

  Scenario: Execute SSM automation document Digito-ExceedRestApiGwQuotaTest_2020-09-21 in failed test
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                            | ResourceType |
      | resource_manager/cloud_formation_templates/RestApiGwTemplate.yml                           | ON_DEMAND    |
      | documents/api-gw/test/rest_api_quota/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-ExceedRestApiGwQuotaTest_2020-09-21" SSM document
    And cache value of "ApiKeyId,ApiHost,ApiPath" "before" SSM automation execution
      | ApiKeyId                                  | ApiHost                                        | ApiPath                                             |
      | {{cfn-output:RestApiGwTemplate>ApiKeyId}} | {{cfn-output:RestApiGwTemplate>RestApiGwHost}} | {{cfn-output:RestApiGwTemplate>RestApiGwStagePath}} |

    When SSM automation document "Digito-ExceedRestApiGwQuotaTest_2020-09-21" executed
      | RestApiGwUsagePlanId                                  | AutomationAssumeRole                                                                 | ApiGw4xxAlarmName                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoExceedRestApiGwQuotaTestAssumeRole}} | {{cfn-output:RestApiGwTemplate>AlwaysOKAlarmName}} |
    And Wait for the SSM automation document "Digito-ExceedRestApiGwQuotaTest_2020-09-21" execution is on step "SetQuotaConfiguration" in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And get API key and perform "12" https "GET" requests with interval "20" seconds

    Then Wait for the SSM automation document "Digito-ExceedRestApiGwQuotaTest_2020-09-21" execution is on step "AssertAlarmToBeRed" in status "TimedOut"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    Then Wait for the SSM automation document "Digito-ExceedRestApiGwQuotaTest_2020-09-21" execution is on step "RollbackCurrentExecution" in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    Then SSM automation document "Digito-ExceedRestApiGwQuotaTest_2020-09-21" execution in status "TimedOut"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    Then assert "CheckIsRollback,AssertAlarmToBeGreenBeforeTest,BackupQuotaConfiguration,SetQuotaConfiguration,RollbackCurrentExecution,AssertAlarmToBeGreen" steps are successfully executed in order
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
