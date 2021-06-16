@api-gw
Feature: SSM automation document Digito-RestApiGwThrottling_2020-09-21

  Scenario: Execute SSM automation document Digito-RestApiGwThrottling_2020-09-21 in rollback without stage name provided
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                             | ResourceType |
      | resource_manager/cloud_formation_templates/RestApiGwTemplate.yml                            | ON_DEMAND    |
      | documents/api-gw/test/throttling-rest/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestApiGwThrottling_2020-09-21" SSM document
    And cache value of "RestApiGwUsagePlanId" "before" SSM automation execution
      | RestApiGwUsagePlanId                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} |
    And cache usage plan rate limit as "RateLimit" and burst limit as "BurstLimit" "before" SSM automation execution

    When SSM automation document "Digito-RestApiGwThrottling_2020-09-21" executed
      | RestApiGwUsagePlanId                                  | AutomationAssumeRole                                                            | ApiGw4xxAlarmName                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestApiGwThrottlingAssumeRole}} | {{cfn-output:RestApiGwTemplate>4XXErrorAlarmName}} |

    Then Wait for the SSM automation document "Digito-RestApiGwThrottling_2020-09-21" execution is on step "AssertAlarmToBeRed" in status "InProgress"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And terminate "Digito-RestApiGwThrottling_2020-09-21" SSM automation document
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    Then Wait for the SSM automation document "Digito-RestApiGwThrottling_2020-09-21" execution is on step "TriggerRollback" in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And SSM automation document "Digito-RestApiGwThrottling_2020-09-21" execution in status "Cancelled"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache rollback execution id
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    Then SSM automation document "Digito-RestApiGwThrottling_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>2}} |
    And assert SSM automation document step "RollbackPreviousExecution" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>2}} |
    And cache usage plan rate limit as "RateLimit" and burst limit as "BurstLimit" "after" SSM automation execution

    Then assert "RateLimit" at "before" became equal to "RateLimit" at "after"
    Then assert "BurstLimit" at "before" became equal to "BurstLimit" at "after"
    Then assert "CheckIsRollback,GetInputsFromPreviousExecution,AssertInputsFromPreviousExecution,PrepareRollbackOfPreviousExecution,RollbackPreviousExecution" steps are successfully executed in order
      | ExecutionId                |
      | {{cache:SsmExecutionId>2}} |


  Scenario: Execute SSM automation document Digito-RestApiGwThrottling_2020-09-21 in rollback with stage name provided
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                             | ResourceType |
      | resource_manager/cloud_formation_templates/RestApiGwTemplate.yml                            | ON_DEMAND    |
      | documents/api-gw/test/throttling-rest/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestApiGwThrottling_2020-09-21" SSM document
    And cache value of "RestApiGwUsagePlanId,RestApiGwStageName,RestApiGwId" "before" SSM automation execution
      | RestApiGwUsagePlanId                                  | RestApiGwStageName                                  | RestApiGwId                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} | {{cfn-output:RestApiGwTemplate>RestApiGwStageName}} | {{cfn-output:RestApiGwTemplate>RestApiGwId}} |
    And cache usage plan rate limit as "RateLimit" and burst limit as "BurstLimit" "before" SSM automation execution

    When SSM automation document "Digito-RestApiGwThrottling_2020-09-21" executed
      | RestApiGwUsagePlanId                                  | RestApiGwStageName                                  | RestApiGwId                                  | AutomationAssumeRole                                                            | ApiGw4xxAlarmName                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} | {{cfn-output:RestApiGwTemplate>RestApiGwStageName}} | {{cfn-output:RestApiGwTemplate>RestApiGwId}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestApiGwThrottlingAssumeRole}} | {{cfn-output:RestApiGwTemplate>4XXErrorAlarmName}} |

    Then Wait for the SSM automation document "Digito-RestApiGwThrottling_2020-09-21" execution is on step "AssertAlarmToBeRed" in status "InProgress"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And terminate "Digito-RestApiGwThrottling_2020-09-21" SSM automation document
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    Then Wait for the SSM automation document "Digito-RestApiGwThrottling_2020-09-21" execution is on step "TriggerRollback" in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And SSM automation document "Digito-RestApiGwThrottling_2020-09-21" execution in status "Cancelled"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache rollback execution id
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    Then SSM automation document "Digito-RestApiGwThrottling_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>2}} |
    And assert SSM automation document step "RollbackPreviousExecution" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>2}} |
    And cache usage plan rate limit as "RateLimit" and burst limit as "BurstLimit" "after" SSM automation execution

    Then assert "RateLimit" at "before" became equal to "RateLimit" at "after"
    Then assert "BurstLimit" at "before" became equal to "BurstLimit" at "after"
    Then assert "CheckIsRollback,GetInputsFromPreviousExecution,AssertInputsFromPreviousExecution,PrepareRollbackOfPreviousExecution,RollbackPreviousExecution" steps are successfully executed in order
      | ExecutionId                |
      | {{cache:SsmExecutionId>2}} |
