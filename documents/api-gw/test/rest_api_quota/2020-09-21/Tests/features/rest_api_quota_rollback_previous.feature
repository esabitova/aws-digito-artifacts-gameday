@api-gw
Feature: SSM automation document Digito-ExceedRestApiGwQuotaTest_2020-09-21

  Scenario: Execute SSM automation document Digito-ExceedRestApiGwQuotaTest_2020-09-21 in rollback test
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                            | ResourceType |
      | resource_manager/cloud_formation_templates/RestApiGwTemplate.yml                           | ON_DEMAND    |
      | documents/api-gw/test/rest_api_quota/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-ExceedRestApiGwQuotaTest_2020-09-21" SSM document
    And cache API GW property "$.quota.limit" as "QuotaLimit" "before" SSM automation execution
      | RestApiGwUsagePlanId                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} |
    And cache API GW property "$.quota.period" as "QuotaPeriod" "before" SSM automation execution
      | RestApiGwUsagePlanId                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} |

    When SSM automation document "Digito-ExceedRestApiGwQuotaTest_2020-09-21" executed
      | RestApiGwUsagePlanId                                  | AutomationAssumeRole                                                                 | ApiGw4xxAlarmName                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoExceedRestApiGwQuotaTestAssumeRole}} | {{cfn-output:RestApiGwTemplate>4XXErrorAlarmName}} |

    Then Wait for the SSM automation document "Digito-ExceedRestApiGwQuotaTest_2020-09-21" execution is on step "AssertAlarmToBeRed" in status "InProgress"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And terminate "Digito-ExceedRestApiGwQuotaTest_2020-09-21" SSM automation document
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    Then Wait for the SSM automation document "Digito-ExceedRestApiGwQuotaTest_2020-09-21" execution is on step "TriggerRollback" in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And SSM automation document "Digito-ExceedRestApiGwQuotaTest_2020-09-21" execution in status "Cancelled"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache rollback execution id
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    Then SSM automation document "Digito-ExceedRestApiGwQuotaTest_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>2}} |
    And assert SSM automation document step "RollbackPreviousExecution" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>2}} |
    And cache API GW property "$.quota.limit" as "QuotaLimit" "after" SSM automation execution
      | RestApiGwUsagePlanId                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} |
    And cache API GW property "$.quota.period" as "QuotaPeriod" "after" SSM automation execution
      | RestApiGwUsagePlanId                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} |

    Then assert "QuotaLimit" at "before" became equal to "QuotaLimit" at "after"
    And assert "QuotaPeriod" at "before" became equal to "QuotaPeriod" at "after"
    And assert "CheckIsRollback,AssertAlarmToBeGreenBeforeTest,BackupQuotaConfiguration,SetQuotaConfiguration,TriggerRollback" steps are successfully executed in order
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And assert "CheckIsRollback,GetInputsFromPreviousExecution,AssertRestApiGwUsagePlanId,PrepareRollbackOfPreviousExecution,RollbackPreviousExecution" steps are successfully executed in order
      | ExecutionId                |
      | {{cache:SsmExecutionId>2}} |
