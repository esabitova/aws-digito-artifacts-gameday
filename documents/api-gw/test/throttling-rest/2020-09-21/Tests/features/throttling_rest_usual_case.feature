@api-gw
Feature: SSM automation document Digito-RestApiGwThrottling_2020-09-21

  Scenario: Execute SSM automation document Digito-RestApiGwThrottling_2020-09-21 without stage name provided
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                             | ResourceType |
      | resource_manager/cloud_formation_templates/RestApiGwTemplate.yml                            | ON_DEMAND    |
      | documents/api-gw/test/throttling-rest/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestApiGwThrottling_2020-09-21" SSM document
    And cache value of "RestApiGwUsagePlanId,ApiKeyId,ApiHost,ApiPath" "before" SSM automation execution
      | RestApiGwUsagePlanId                                  | ApiKeyId                                  | ApiHost                                        | ApiPath                                             |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} | {{cfn-output:RestApiGwTemplate>ApiKeyId}} | {{cfn-output:RestApiGwTemplate>RestApiGwHost}} | {{cfn-output:RestApiGwTemplate>RestApiGwStagePath}} |
    And cache usage plan rate limit as "OldRateLimit" and burst limit as "OldBurstLimit" "before" SSM automation execution

    When SSM automation document "Digito-RestApiGwThrottling_2020-09-21" executed
      | RestApiGwUsagePlanId                                  | AutomationAssumeRole                                                            | ApiGw4xxAlarmName                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestApiGwThrottlingAssumeRole}} | {{cfn-output:RestApiGwTemplate>4XXErrorAlarmName}} |
    And Wait for the SSM automation document "Digito-RestApiGwThrottling_2020-09-21" execution is on step "SetThrottlingConfiguration" in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And get API key and perform "24" https "GET" requests with interval "10" seconds
    And cache usage plan rate limit as "AppliedRateLimit" and burst limit as "AppliedBurstLimit" "after" SSM automation execution
    And SSM automation document "Digito-RestApiGwThrottling_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache usage plan rate limit as "ActualRateLimit" and burst limit as "ActualBurstLimit" "after" SSM automation execution

    Then assert "OldRateLimit" at "before" became equal to "ActualRateLimit" at "after"
    And assert "OldBurstLimit" at "before" became equal to "ActualBurstLimit" at "after"
    And assert "CheckIsRollback,AssertAlarmToBeGreenBeforeTest,BackupThrottlingConfiguration,SetThrottlingConfiguration,AssertAlarmToBeRed,RollbackCurrentExecution,AssertAlarmToBeGreen" steps are successfully executed in order
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |


  Scenario: Execute SSM automation document Digito-RestApiGwThrottling_2020-09-21 with stage name provided
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                             | ResourceType |
      | resource_manager/cloud_formation_templates/RestApiGwTemplate.yml                            | ON_DEMAND    |
      | documents/api-gw/test/throttling-rest/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestApiGwThrottling_2020-09-21" SSM document
    And cache value of "RestApiGwUsagePlanId,RestApiGwStageName,RestApiGwId,ApiKeyId,ApiHost,ApiPath" "before" SSM automation execution
      | RestApiGwUsagePlanId                                  | RestApiGwStageName                                  | RestApiGwId                                  | ApiKeyId                                  | ApiHost                                        | ApiPath                                             |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} | {{cfn-output:RestApiGwTemplate>RestApiGwStageName}} | {{cfn-output:RestApiGwTemplate>RestApiGwId}} | {{cfn-output:RestApiGwTemplate>ApiKeyId}} | {{cfn-output:RestApiGwTemplate>RestApiGwHost}} | {{cfn-output:RestApiGwTemplate>RestApiGwStagePath}} |
    And cache usage plan rate limit as "OldRateLimit" and burst limit as "OldBurstLimit" "before" SSM automation execution

    When SSM automation document "Digito-RestApiGwThrottling_2020-09-21" executed
      | RestApiGwUsagePlanId                                  | RestApiGwStageName                                  | RestApiGwId                                  | AutomationAssumeRole                                                            | ApiGw4xxAlarmName                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} | {{cfn-output:RestApiGwTemplate>RestApiGwStageName}} | {{cfn-output:RestApiGwTemplate>RestApiGwId}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestApiGwThrottlingAssumeRole}} | {{cfn-output:RestApiGwTemplate>4XXErrorAlarmName}} |
    And Wait for the SSM automation document "Digito-RestApiGwThrottling_2020-09-21" execution is on step "SetThrottlingConfiguration" in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And get API key and perform "24" https "GET" requests with interval "10" seconds
    And cache usage plan rate limit as "AppliedRateLimit" and burst limit as "AppliedBurstLimit" "after" SSM automation execution
    And SSM automation document "Digito-RestApiGwThrottling_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache usage plan rate limit as "ActualRateLimit" and burst limit as "ActualBurstLimit" "after" SSM automation execution

    Then assert "OldRateLimit" at "before" became equal to "ActualRateLimit" at "after"
    And assert "OldBurstLimit" at "before" became equal to "ActualBurstLimit" at "after"
    And assert "CheckIsRollback,AssertAlarmToBeGreenBeforeTest,BackupThrottlingConfiguration,SetThrottlingConfiguration,AssertAlarmToBeRed,RollbackCurrentExecution,AssertAlarmToBeGreen" steps are successfully executed in order
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
