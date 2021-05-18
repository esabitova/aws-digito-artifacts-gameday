@api-gw
Feature: SSM automation document to change REST API GW usage plan limits

  Scenario: Change throttling settings for REST API Gateway with ForceExecution=True and without provided stage name
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                            | ResourceType |
      | resource_manager/cloud_formation_templates/RestApiGwTemplate.yml                                           | ON_DEMAND    |
      | documents/api-gw/sop/change_throttling_settings_rest/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestApiGwChangeThrottlingSettings_2020-10-26" SSM document
    And cache value of "RestApiGwUsagePlanId" "before" SSM automation execution for teardown
      | RestApiGwUsagePlanId                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} |
    And cache usage plan rate limit as "OldRateLimit" and burst limit as "OldBurstLimit" "before" SSM automation execution
    And generate different value of "Limit" than "OldRateLimit" from "80" to "120" as "ExpectedRateLimit" "before" SSM automation execution
      | OldRateLimit                  |
      | {{cache:before>OldRateLimit}} |
    And generate different value of "Limit" than "OldBurstLimit" from "80" to "120" as "ExpectedBurstLimit" "before" SSM automation execution
      | OldBurstLimit                  |
      | {{cache:before>OldBurstLimit}} |

    When SSM automation document "Digito-RestApiGwChangeThrottlingSettings_2020-10-26" executed
      | RestApiGwUsagePlanId                                  | ForceExecution | RestApiGwThrottlingRate            | RestApiGwThrottlingBurst            | AutomationAssumeRole                                                                             |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} | true           | {{cache:before>ExpectedRateLimit}} | {{cache:before>ExpectedBurstLimit}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestApiGwChangeThrottlingSettingsAssumeRoleArn}} |
    And SSM automation document "Digito-RestApiGwChangeThrottlingSettings_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache usage plan rate limit as "ActualRateLimit" and burst limit as "ActualBurstLimit" "after" SSM automation execution

    Then assert "ExpectedRateLimit" at "before" became equal to "ActualRateLimit" at "after"
    And assert "ExpectedBurstLimit" at "before" became equal to "ActualBurstLimit" at "after"


  Scenario: Change throttling settings for REST API Gateway with ForceExecution=True and with provided stage name
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                            | ResourceType |
      | resource_manager/cloud_formation_templates/RestApiGwTemplate.yml                                           | ON_DEMAND    |
      | documents/api-gw/sop/change_throttling_settings_rest/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestApiGwChangeThrottlingSettings_2020-10-26" SSM document
    And cache value of "RestApiGwUsagePlanId,RestApiGwStageName,RestApiGwId" "before" SSM automation execution for teardown
      | RestApiGwUsagePlanId                                  | RestApiGwStageName                                  | RestApiGwId                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} | {{cfn-output:RestApiGwTemplate>RestApiGwStageName}} | {{cfn-output:RestApiGwTemplate>RestApiGwId}} |
    And cache usage plan rate limit as "OldRateLimit" and burst limit as "OldBurstLimit" "before" SSM automation execution
    And generate different value of "Limit" than "OldRateLimit" from "80" to "120" as "ExpectedRateLimit" "before" SSM automation execution
      | OldRateLimit                  |
      | {{cache:before>OldRateLimit}} |
    And generate different value of "Limit" than "OldBurstLimit" from "80" to "120" as "ExpectedBurstLimit" "before" SSM automation execution
      | OldBurstLimit                  |
      | {{cache:before>OldBurstLimit}} |

    When SSM automation document "Digito-RestApiGwChangeThrottlingSettings_2020-10-26" executed
      | RestApiGwUsagePlanId                                  | ForceExecution | RestApiGwStageName                                  | RestApiGwId                                  | RestApiGwThrottlingRate            | RestApiGwThrottlingBurst            | AutomationAssumeRole                                                                             |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} | true           | {{cfn-output:RestApiGwTemplate>RestApiGwStageName}} | {{cfn-output:RestApiGwTemplate>RestApiGwId}} | {{cache:before>ExpectedRateLimit}} | {{cache:before>ExpectedBurstLimit}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestApiGwChangeThrottlingSettingsAssumeRoleArn}} |
    And SSM automation document "Digito-RestApiGwChangeThrottlingSettings_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache usage plan rate limit as "ActualRateLimit" and burst limit as "ActualBurstLimit" "after" SSM automation execution

    Then assert "ExpectedRateLimit" at "before" became equal to "ActualRateLimit" at "after"
    And assert "ExpectedBurstLimit" at "before" became equal to "ActualBurstLimit" at "after"


  Scenario: Change throttling settings for REST API Gateway with ForceExecution=True, without provided stage name and with new rate limit more than 50%
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                            | ResourceType |
      | resource_manager/cloud_formation_templates/RestApiGwTemplate.yml                                           | ON_DEMAND    |
      | documents/api-gw/sop/change_throttling_settings_rest/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestApiGwChangeThrottlingSettings_2020-10-26" SSM document
    And cache value of "RestApiGwUsagePlanId" "before" SSM automation execution for teardown
      | RestApiGwUsagePlanId                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} |
    And cache usage plan rate limit as "OldRateLimit" and burst limit as "OldBurstLimit" "before" SSM automation execution
    And generate different value of "Limit" than "OldRateLimit" from "200" to "500" as "ExpectedRateLimit" "before" SSM automation execution
      | OldRateLimit                  |
      | {{cache:before>OldRateLimit}} |
    And generate different value of "Limit" than "OldBurstLimit" from "80" to "120" as "ExpectedBurstLimit" "before" SSM automation execution
      | OldBurstLimit                  |
      | {{cache:before>OldBurstLimit}} |

    When SSM automation document "Digito-RestApiGwChangeThrottlingSettings_2020-10-26" executed
      | RestApiGwUsagePlanId                                  | ForceExecution | RestApiGwThrottlingRate            | RestApiGwThrottlingBurst            | AutomationAssumeRole                                                                             |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} | true           | {{cache:before>ExpectedRateLimit}} | {{cache:before>ExpectedBurstLimit}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestApiGwChangeThrottlingSettingsAssumeRoleArn}} |
    And SSM automation document "Digito-RestApiGwChangeThrottlingSettings_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache usage plan rate limit as "ActualRateLimit" and burst limit as "ActualBurstLimit" "after" SSM automation execution

    Then assert "ExpectedRateLimit" at "before" became equal to "ActualRateLimit" at "after"
    And assert "ExpectedBurstLimit" at "before" became equal to "ActualBurstLimit" at "after"
