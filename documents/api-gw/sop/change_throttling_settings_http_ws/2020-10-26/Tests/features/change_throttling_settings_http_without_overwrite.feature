@api-gw
Feature: SSM automation document to change HTTP or WS API GW route throttling settings

  Scenario: Change throttling settings for HTTP API Gateway with ForceExecution=False and without provided route key
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                               | ResourceType |
      | resource_manager/cloud_formation_templates/HTTPWSApiGwTemplate.yml                                            | ON_DEMAND    |
      | documents/api-gw/sop/change_throttling_settings_http_ws/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-ChangeThrottlingSettingsHttpWs_2020-10-26" SSM document
    And cache default route throttling rate limit as "RateLimit" and burst limit as "BurstLimit" "before" SSM automation execution
      | HttpWsApiGwId                                  | HttpWsStageName                                  |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageName}} |
    And prepare default route settings for teardown
      | HttpWsApiGwId                                  | HttpWsStageName                                  | BackupRateLimit            | BackupBurstLimit            |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageName}} | {{cache:before>RateLimit}} | {{cache:before>BurstLimit}} |
    And generate different value of "Limit" than "OldRateLimit" from "6000" to "7000" as "ExpectedRateLimit" "before" SSM automation execution
      | OldRateLimit               |
      | {{cache:before>RateLimit}} |
    And generate different value of "Limit" than "OldBurstLimit" from "3000" to "4000" as "ExpectedBurstLimit" "before" SSM automation execution
      | OldBurstLimit               |
      | {{cache:before>BurstLimit}} |

    When SSM automation document "Digito-ChangeThrottlingSettingsHttpWs_2020-10-26" executed
      | HttpWsApiGwId                                  | HttpWsStageName                                  | HttpWsThrottlingRate               | HttpWsThrottlingBurst               | AutomationAssumeRole                                                                            |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageName}} | {{cache:before>ExpectedRateLimit}} | {{cache:before>ExpectedBurstLimit}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoApiGwChangeThrottlingSettingsHttpWsAssumeRole}} |

    Then SSM automation document "Digito-ChangeThrottlingSettingsHttpWs_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache default route throttling rate limit as "RateLimit" and burst limit as "BurstLimit" "after" SSM automation execution
      | HttpWsApiGwId                                  | HttpWsStageName                                  |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageName}} |
    And assert "ExpectedRateLimit" at "before" became equal to "RateLimit" at "after"
    And assert "ExpectedBurstLimit" at "before" became equal to "BurstLimit" at "after"


  Scenario: Change throttling settings for HTTP API Gateway with ForceExecution=False and with the specified route key
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                               | ResourceType |
      | resource_manager/cloud_formation_templates/HTTPWSApiGwTemplate.yml                                            | ON_DEMAND    |
      | documents/api-gw/sop/change_throttling_settings_http_ws/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-ChangeThrottlingSettingsHttpWs_2020-10-26" SSM document
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

    When SSM automation document "Digito-ChangeThrottlingSettingsHttpWs_2020-10-26" executed
      | HttpWsApiGwId                                  | HttpWsStageName                                  | HttpWsThrottlingRate               | HttpWsThrottlingBurst               | HttpWsRouteKey | AutomationAssumeRole                                                                            |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageName}} | {{cache:before>ExpectedRateLimit}} | {{cache:before>ExpectedBurstLimit}} | POST /test     | {{cfn-output:AutomationAssumeRoleTemplate>DigitoApiGwChangeThrottlingSettingsHttpWsAssumeRole}} |

    Then SSM automation document "Digito-ChangeThrottlingSettingsHttpWs_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache route throttling rate limit as "RateLimit" and burst limit as "BurstLimit" "after" SSM automation execution
      | HttpWsApiGwId                                  | HttpWsStageName                                  | HttpWsRouteKey |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageName}} | POST /test     |
    And assert "ExpectedRateLimit" at "before" became equal to "RateLimit" at "after"
    And assert "ExpectedBurstLimit" at "before" became equal to "BurstLimit" at "after"