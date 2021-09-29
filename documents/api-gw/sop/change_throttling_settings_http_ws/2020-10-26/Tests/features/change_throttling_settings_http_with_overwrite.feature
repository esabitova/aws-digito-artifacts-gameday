@api-gw
Feature: SSM automation document to change HTTP or WS API GW route throttling settings

  Scenario: Change throttling settings for HTTP API Gateway with no throttling, ForceExecution=True and with the specified route key
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                               | ResourceType |
      | resource_manager/cloud_formation_templates/HTTPWSApiGwTemplate.yml                                            | ON_DEMAND    |
      | documents/api-gw/sop/change_throttling_settings_http_ws/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-ChangeHttpWsApiGwThrottlingSettingsSOP_2020-10-26" SSM document
    And cache route throttling rate limit as "RateLimit" and burst limit as "BurstLimit" "before" SSM automation execution
      | HttpWsApiGwId                                  | HttpWsStageName                                  | HttpWsRouteKey |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageName}} | POST /test     |
    And prepare route settings for teardown
      | HttpWsApiGwId                                  | HttpWsStageName                                  | BackupRateLimit            | BackupBurstLimit            | HttpWsRouteKey |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageName}} | {{cache:before>RateLimit}} | {{cache:before>BurstLimit}} | POST /test     |
    And generate different value of "Limit" than "OldRateLimit" from "6000" to "7000" as "ExpectedRateLimit" "before" SSM automation execution
      | OldRateLimit               |
      | {{cache:before>RateLimit}} |
    And generate different value of "Limit" than "OldBurstLimit" from "3000" to "4000" as "ExpectedBurstLimit" "before" SSM automation execution
      | OldBurstLimit               |
      | {{cache:before>BurstLimit}} |
    When SSM automation document "Digito-ChangeHttpWsApiGwThrottlingSettingsSOP_2020-10-26" executed
      | HttpWsApiGwId                                  | HttpWsStageName                                  | HttpWsThrottlingRate               | HttpWsThrottlingBurst               | HttpWsRouteKey | ForceExecution | AutomationAssumeRole                                                                               |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageName}} | {{cache:before>ExpectedRateLimit}} | {{cache:before>ExpectedBurstLimit}} | POST /test     | true           | {{cfn-output:AutomationAssumeRoleTemplate>DigitoChangeHttpWsApiGwThrottlingSettingsSOPAssumeRole}} |
    Then SSM automation document "Digito-ChangeHttpWsApiGwThrottlingSettingsSOP_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache route throttling rate limit as "RateLimit" and burst limit as "BurstLimit" "after" SSM automation execution
      | HttpWsApiGwId                                  | HttpWsStageName                                  | HttpWsRouteKey |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageName}} | POST /test     |
    And assert "ExpectedRateLimit" at "before" became equal to "RateLimit" at "after"
    And assert "ExpectedBurstLimit" at "before" became equal to "BurstLimit" at "after"



  Scenario: Change throttling settings for HTTP API Gateway with throttling enabled, ForceExecution=True and with the specified route key
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                               | ResourceType |
      | resource_manager/cloud_formation_templates/HTTPWSApiGwTemplate.yml                                            | ON_DEMAND    |
      | documents/api-gw/sop/change_throttling_settings_http_ws/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-ChangeHttpWsApiGwThrottlingSettingsSOP_2020-10-26" SSM document
    And cache route throttling rate limit as "RateLimit" and burst limit as "BurstLimit" "before" SSM automation execution
      | HttpWsApiGwId                                  | HttpWsStageName                                           | HttpWsRouteKey |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageNameThrottled}} | POST /test     |
    And prepare route settings for teardown
      | HttpWsApiGwId                                  | HttpWsStageName                                           | BackupRateLimit            | BackupBurstLimit            | HttpWsRouteKey |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageNameThrottled}} | {{cache:before>RateLimit}} | {{cache:before>BurstLimit}} | POST /test     |
    And generate different value of "Limit" than "OldRateLimit" from "70" to "80" as "ExpectedRateLimit" "before" SSM automation execution
      | OldRateLimit               |
      | {{cache:before>RateLimit}} |
    And generate different value of "Limit" than "OldBurstLimit" from "70" to "80" as "ExpectedBurstLimit" "before" SSM automation execution
      | OldBurstLimit               |
      | {{cache:before>BurstLimit}} |
    When SSM automation document "Digito-ChangeHttpWsApiGwThrottlingSettingsSOP_2020-10-26" executed
      | HttpWsApiGwId                                  | HttpWsStageName                                           | HttpWsThrottlingRate               | HttpWsThrottlingBurst               | HttpWsRouteKey | ForceExecution | AutomationAssumeRole                                                                               |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageNameThrottled}} | {{cache:before>ExpectedRateLimit}} | {{cache:before>ExpectedBurstLimit}} | POST /test     | true           | {{cfn-output:AutomationAssumeRoleTemplate>DigitoChangeHttpWsApiGwThrottlingSettingsSOPAssumeRole}} |
    Then SSM automation document "Digito-ChangeHttpWsApiGwThrottlingSettingsSOP_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache route throttling rate limit as "RateLimit" and burst limit as "BurstLimit" "after" SSM automation execution
      | HttpWsApiGwId                                  | HttpWsStageName                                           | HttpWsRouteKey |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageNameThrottled}} | POST /test     |
    And assert "ExpectedRateLimit" at "before" became equal to "RateLimit" at "after"
    And assert "ExpectedBurstLimit" at "before" became equal to "BurstLimit" at "after"



  Scenario: Change rate limit above 50% for HTTP API Gateway with throttling enabled, ForceExecution=True and with the specified route key
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                               | ResourceType |
      | resource_manager/cloud_formation_templates/HTTPWSApiGwTemplate.yml                                            | ON_DEMAND    |
      | documents/api-gw/sop/change_throttling_settings_http_ws/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-ChangeHttpWsApiGwThrottlingSettingsSOP_2020-10-26" SSM document
    And cache route throttling rate limit as "RateLimit" and burst limit as "BurstLimit" "before" SSM automation execution
      | HttpWsApiGwId                                  | HttpWsStageName                                           | HttpWsRouteKey |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageNameThrottled}} | POST /test     |
    And prepare route settings for teardown
      | HttpWsApiGwId                                  | HttpWsStageName                                           | BackupRateLimit            | BackupBurstLimit            | HttpWsRouteKey |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageNameThrottled}} | {{cache:before>RateLimit}} | {{cache:before>BurstLimit}} | POST /test     |
    And generate different value of "Limit" than "OldRateLimit" from "10" to "20" as "ExpectedRateLimit" "before" SSM automation execution
      | OldRateLimit               |
      | {{cache:before>RateLimit}} |
    And generate different value of "Limit" than "OldBurstLimit" from "70" to "80" as "ExpectedBurstLimit" "before" SSM automation execution
      | OldBurstLimit               |
      | {{cache:before>BurstLimit}} |
    When SSM automation document "Digito-ChangeHttpWsApiGwThrottlingSettingsSOP_2020-10-26" executed
      | HttpWsApiGwId                                  | HttpWsStageName                                           | HttpWsThrottlingRate               | HttpWsThrottlingBurst               | HttpWsRouteKey | ForceExecution | AutomationAssumeRole                                                                               |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageNameThrottled}} | {{cache:before>ExpectedRateLimit}} | {{cache:before>ExpectedBurstLimit}} | POST /test     | true           | {{cfn-output:AutomationAssumeRoleTemplate>DigitoChangeHttpWsApiGwThrottlingSettingsSOPAssumeRole}} |
    Then SSM automation document "Digito-ChangeHttpWsApiGwThrottlingSettingsSOP_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache route throttling rate limit as "RateLimit" and burst limit as "BurstLimit" "after" SSM automation execution
      | HttpWsApiGwId                                  | HttpWsStageName                                           | HttpWsRouteKey |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageNameThrottled}} | POST /test     |
    And assert "ExpectedRateLimit" at "before" became equal to "RateLimit" at "after"
    And assert "ExpectedBurstLimit" at "before" became equal to "BurstLimit" at "after"



  Scenario: Change burst limit above 50% for HTTP API Gateway with throttling enabled, ForceExecution=True and with the specified route key
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                               | ResourceType |
      | resource_manager/cloud_formation_templates/HTTPWSApiGwTemplate.yml                                            | ON_DEMAND    |
      | documents/api-gw/sop/change_throttling_settings_http_ws/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-ChangeHttpWsApiGwThrottlingSettingsSOP_2020-10-26" SSM document
    And cache route throttling rate limit as "RateLimit" and burst limit as "BurstLimit" "before" SSM automation execution
      | HttpWsApiGwId                                  | HttpWsStageName                                           | HttpWsRouteKey |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageNameThrottled}} | POST /test     |
    And prepare route settings for teardown
      | HttpWsApiGwId                                  | HttpWsStageName                                           | BackupRateLimit            | BackupBurstLimit            | HttpWsRouteKey |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageNameThrottled}} | {{cache:before>RateLimit}} | {{cache:before>BurstLimit}} | POST /test     |
    And generate different value of "Limit" than "OldRateLimit" from "70" to "80" as "ExpectedRateLimit" "before" SSM automation execution
      | OldRateLimit               |
      | {{cache:before>RateLimit}} |
    And generate different value of "Limit" than "OldBurstLimit" from "10" to "20" as "ExpectedBurstLimit" "before" SSM automation execution
      | OldBurstLimit               |
      | {{cache:before>BurstLimit}} |
    When SSM automation document "Digito-ChangeHttpWsApiGwThrottlingSettingsSOP_2020-10-26" executed
      | HttpWsApiGwId                                  | HttpWsStageName                                           | HttpWsThrottlingRate               | HttpWsThrottlingBurst               | HttpWsRouteKey | ForceExecution | AutomationAssumeRole                                                                               |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageNameThrottled}} | {{cache:before>ExpectedRateLimit}} | {{cache:before>ExpectedBurstLimit}} | POST /test     | true           | {{cfn-output:AutomationAssumeRoleTemplate>DigitoChangeHttpWsApiGwThrottlingSettingsSOPAssumeRole}} |
    Then SSM automation document "Digito-ChangeHttpWsApiGwThrottlingSettingsSOP_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache route throttling rate limit as "RateLimit" and burst limit as "BurstLimit" "after" SSM automation execution
      | HttpWsApiGwId                                  | HttpWsStageName                                           | HttpWsRouteKey |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageNameThrottled}} | POST /test     |
    And assert "ExpectedRateLimit" at "before" became equal to "RateLimit" at "after"
    And assert "ExpectedBurstLimit" at "before" became equal to "BurstLimit" at "after"



  Scenario: Fail to change rate limit above account quota for HTTP API Gateway with throttling enabled, ForceExecution=True and with the specified route key
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                               | ResourceType |
      | resource_manager/cloud_formation_templates/HTTPWSApiGwTemplate.yml                                            | ON_DEMAND    |
      | documents/api-gw/sop/change_throttling_settings_http_ws/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-ChangeHttpWsApiGwThrottlingSettingsSOP_2020-10-26" SSM document
    And cache route throttling rate limit as "RateLimit" and burst limit as "BurstLimit" "before" SSM automation execution
      | HttpWsApiGwId                                  | HttpWsStageName                                           | HttpWsRouteKey |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageNameThrottled}} | POST /test     |
    And prepare route settings for teardown
      | HttpWsApiGwId                                  | HttpWsStageName                                           | BackupRateLimit            | BackupBurstLimit            | HttpWsRouteKey |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageNameThrottled}} | {{cache:before>RateLimit}} | {{cache:before>BurstLimit}} | POST /test     |
    And generate different value of "Limit" than "OldBurstLimit" from "70" to "80" as "ExpectedBurstLimit" "before" SSM automation execution
      | OldBurstLimit               |
      | {{cache:before>BurstLimit}} |
    When SSM automation document "Digito-ChangeHttpWsApiGwThrottlingSettingsSOP_2020-10-26" executed
      | HttpWsApiGwId                                  | HttpWsStageName                                           | HttpWsThrottlingRate | HttpWsThrottlingBurst               | HttpWsRouteKey | ForceExecution | AutomationAssumeRole                                                                               |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageNameThrottled}} | 20000                | {{cache:before>ExpectedBurstLimit}} | POST /test     | true           | {{cfn-output:AutomationAssumeRoleTemplate>DigitoChangeHttpWsApiGwThrottlingSettingsSOPAssumeRole}} |
    Then SSM automation document "Digito-ChangeHttpWsApiGwThrottlingSettingsSOP_2020-10-26" execution in status "Failed"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache route throttling rate limit as "RateLimit" and burst limit as "BurstLimit" "after" SSM automation execution
      | HttpWsApiGwId                                  | HttpWsStageName                                           | HttpWsRouteKey |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageNameThrottled}} | POST /test     |
    And assert "BurstLimit" at "before" became equal to "RateLimit" at "after"
    And assert "BurstLimit" at "before" became equal to "BurstLimit" at "after"



  Scenario: Fail to change burst limit above account quota for HTTP API Gateway with throttling enabled, ForceExecution=True and with the specified route key
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                               | ResourceType |
      | resource_manager/cloud_formation_templates/HTTPWSApiGwTemplate.yml                                            | ON_DEMAND    |
      | documents/api-gw/sop/change_throttling_settings_http_ws/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-ChangeHttpWsApiGwThrottlingSettingsSOP_2020-10-26" SSM document
    And cache route throttling rate limit as "RateLimit" and burst limit as "BurstLimit" "before" SSM automation execution
      | HttpWsApiGwId                                  | HttpWsStageName                                           | HttpWsRouteKey |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageNameThrottled}} | POST /test     |
    And prepare route settings for teardown
      | HttpWsApiGwId                                  | HttpWsStageName                                           | BackupRateLimit            | BackupBurstLimit            | HttpWsRouteKey |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageNameThrottled}} | {{cache:before>RateLimit}} | {{cache:before>BurstLimit}} | POST /test     |
    And generate different value of "Limit" than "OldRateLimit" from "70" to "80" as "ExpectedRateLimit" "before" SSM automation execution
      | OldRateLimit               |
      | {{cache:before>RateLimit}} |
    When SSM automation document "Digito-ChangeHttpWsApiGwThrottlingSettingsSOP_2020-10-26" executed
      | HttpWsApiGwId                                  | HttpWsStageName                                           | HttpWsThrottlingRate               | HttpWsThrottlingBurst | HttpWsRouteKey | ForceExecution | AutomationAssumeRole                                                                               |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageNameThrottled}} | {{cache:before>ExpectedRateLimit}} | 10000                 | POST /test     | true           | {{cfn-output:AutomationAssumeRoleTemplate>DigitoChangeHttpWsApiGwThrottlingSettingsSOPAssumeRole}} |
    Then SSM automation document "Digito-ChangeHttpWsApiGwThrottlingSettingsSOP_2020-10-26" execution in status "Failed"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache route throttling rate limit as "RateLimit" and burst limit as "BurstLimit" "after" SSM automation execution
      | HttpWsApiGwId                                  | HttpWsStageName                                           | HttpWsRouteKey |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageNameThrottled}} | POST /test     |
    And assert "BurstLimit" at "before" became equal to "RateLimit" at "after"
    And assert "BurstLimit" at "before" became equal to "BurstLimit" at "after"