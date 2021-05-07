@api-gw
Feature: SSM automation document to change REST API GW usage plan limits

  Scenario: Change throttling settings for REST API Gateway with ForceExecution=False and without provided stage name
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                               | ResourceType |
      | resource_manager/cloud_formation_templates/RestApiGwTemplate.yml                                           | ON_DEMAND    |
      | documents/api-gw/sop/change_throttling_settings_rest/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestApiGwChangeThrottlingSettings_2020-10-26" SSM document
    And cache API GW property "$.throttle.rateLimit" as "OldRateLimit" "before" SSM automation execution
      | RestApiGwUsagePlanId                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} |
    And cache API GW property "$.throttle.burstLimit" as "OldBurstLimit" "before" SSM automation execution
      | RestApiGwUsagePlanId                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} |
    And generate different value of "Limit" than "OldRateLimit" from "80" to "120" as "ExpectedRateLimit" "before" SSM automation execution
      | OldRateLimit                  |
      | {{cache:before>OldRateLimit}} |
    And generate different value of "Limit" than "OldBurstLimit" from "80" to "120" as "ExpectedBurstLimit" "before" SSM automation execution
      | OldBurstLimit                  |
      | {{cache:before>OldBurstLimit}} |
    When SSM automation document "Digito-RestApiGwChangeThrottlingSettings_2020-10-26" executed
      | RestApiGwUsagePlanId                                  | RestApiGwThrottlingRate            | RestApiGwThrottlingBurst            | AutomationAssumeRole                                                                             |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} | {{cache:before>ExpectedRateLimit}} | {{cache:before>ExpectedBurstLimit}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestApiGwChangeThrottlingSettingsAssumeRoleArn}} |
    And SSM automation document "Digito-RestApiGwChangeThrottlingSettings_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache API GW property "$.throttle.rateLimit" as "ActualRateLimit" "after" SSM automation execution
      | RestApiGwUsagePlanId                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} |
    And cache API GW property "$.throttle.burstLimit" as "ActualBurstLimit" "after" SSM automation execution
      | RestApiGwUsagePlanId                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} |
    Then assert "ExpectedRateLimit" at "before" became equal to "ActualRateLimit" at "after"
    Then assert "ExpectedBurstLimit" at "before" became equal to "ActualBurstLimit" at "after"

