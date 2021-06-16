@api-gw
Feature: SSM automation document Digito-RestApiGwQuota_2020-09-21

  Scenario: Execute SSM automation document Digito-RestApiGwQuota_2020-09-21
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                            | ResourceType |
      | resource_manager/cloud_formation_templates/RestApiGwTemplate.yml                           | ON_DEMAND    |
      | documents/api-gw/test/rest_api_quota/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestApiGwQuota_2020-09-21" SSM document
    And cache API GW property "$.quota.limit" as "QuotaLimit" "before" SSM automation execution
      | RestApiGwUsagePlanId                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} |
    And cache API GW property "$.quota.period" as "QuotaPeriod" "before" SSM automation execution
      | RestApiGwUsagePlanId                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} |

    When SSM automation document "Digito-RestApiGwQuota_2020-09-21" executed
      | RestApiGwUsagePlanId                                  | AutomationAssumeRole                                                       | ApiGw4xxAlarmName                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestApiGwQuotaAssumeRole}} | {{cfn-output:RestApiGwTemplate>4XXErrorAlarmName}} |
    And Wait for the SSM automation document "Digito-RestApiGwQuota_2020-09-21" execution is on step "SetQuotaConfiguration" in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And get value of API key "ApiKeyId" and perform "12" http requests with delay "20" seconds using stage URL "RestApiGwStageUrl"
      | ApiKeyId                                  | RestApiGwStageUrl                                  |
      | {{cfn-output:RestApiGwTemplate>ApiKeyId}} | {{cfn-output:RestApiGwTemplate>RestApiGwStageUrl}} |
    And SSM automation document "Digito-RestApiGwQuota_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache API GW property "$.quota.limit" as "QuotaLimit" "after" SSM automation execution
      | RestApiGwUsagePlanId                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} |
    And cache API GW property "$.quota.period" as "QuotaPeriod" "after" SSM automation execution
      | RestApiGwUsagePlanId                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} |

    Then assert "QuotaLimit" at "before" became equal to "QuotaLimit" at "after"
    And assert "QuotaPeriod" at "before" became equal to "QuotaPeriod" at "after"
    And assert "CheckIsRollback,AssertAlarmToBeGreenBeforeTest,BackupQuotaConfiguration,SetQuotaConfiguration,AssertAlarmToBeRed,RollbackCurrentExecution,AssertAlarmToBeGreen" steps are successfully executed in order
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
