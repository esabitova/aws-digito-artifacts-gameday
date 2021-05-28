@api-gw
Feature: SSM automation document Digito-RestApiGwQuota_2020-09-21

  Scenario: Execute SSM automation document Digito-RestApiGwQuota_2020-09-21 in failed test
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                            | ResourceType |
      | resource_manager/cloud_formation_templates/RestApiGwTemplate.yml                           | ON_DEMAND    |
      | documents/api-gw/test/rest_api_quota/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestApiGwQuota_2020-09-21" SSM document

    When SSM automation document "Digito-RestApiGwQuota_2020-09-21" executed
      | RestApiGwUsagePlanId                                  | AutomationAssumeRole                                                       | ApiGw4xxAlarmName                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestApiGwQuotaAssumeRole}} | {{cfn-output:RestApiGwTemplate>5XXErrorAlarmName}} |
    And Wait for the SSM automation document "Digito-RestApiGwQuota_2020-09-21" execution is on step "SetQuotaConfiguration" in status "Success" for "300" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And get value of API key "ApiKeyId" and perform "12" http requests with delay "20" seconds using stage URL "RestApiGwStageUrl"
      | ApiKeyId                                  | RestApiGwStageUrl                                  |
      | {{cfn-output:RestApiGwTemplate>ApiKeyId}} | {{cfn-output:RestApiGwTemplate>RestApiGwStageUrl}} |

    Then Wait for the SSM automation document "Digito-RestApiGwQuota_2020-09-21" execution is on step "AssertAlarmToBeRed" in status "TimedOut" for "990" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    Then Wait for the SSM automation document "Digito-RestApiGwQuota_2020-09-21" execution is on step "RollbackCurrentExecution" in status "Success" for "300" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    Then SSM automation document "Digito-RestApiGwQuota_2020-09-21" execution in status "TimedOut"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    Then assert "CheckIsRollback,AssertAlarmToBeGreenBeforeTest,BackupQuotaConfiguration,SetQuotaConfiguration,RollbackCurrentExecution,AssertAlarmToBeGreen" steps are successfully executed in order
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
