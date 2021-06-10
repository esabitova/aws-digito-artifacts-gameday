@api-gw
Feature: SSM automation document Digito-ThrottlingHttpWs_2020-09-21

  Scenario: Execute SSM automation document Digito-ThrottlingHttpWs_2020-09-21 for WS API to test failure case
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                | ResourceType |
      | resource_manager/cloud_formation_templates/HTTPWSApiGwTemplate.yml                             | ON_DEMAND    |
      | documents/api-gw/test/throttling-http-ws/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-ThrottlingHttpWs_2020-09-21" SSM document
    And cache default route throttling rate limit as "RateLimit" and burst limit as "BurstLimit" "before" SSM automation execution
      | HttpWsApiGwId                                | HttpWsStageName                                         |
      | {{cfn-output:HTTPWSApiGwTemplate>WsApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>WsStageNameThrottled}} |

    When SSM automation document "Digito-ThrottlingHttpWs_2020-09-21" executed
      | HttpWsApiGwId                                | HttpWsStageName                                         | AutomationAssumeRole                                                              | 4xxAlarmName                                           |
      | {{cfn-output:HTTPWSApiGwTemplate>WsApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>WsStageNameThrottled}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoApiGwThrottlingHttpWsAssumeRole}} | {{cfn-output:HTTPWSApiGwTemplate>Ws4XXErrorAlarmName}} |
    And Wait for the SSM automation document "Digito-ThrottlingHttpWs_2020-09-21" execution is on step "RollbackCurrentExecution" in status "Success" for "1200" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And call ws endpoint "WsEndpoint" "12" times with delay "20" seconds
      | WsEndpoint                                                |
      | {{cfn-output:HTTPWSApiGwTemplate>WsApiThrottledEndpoint}} |

    Then SSM automation document "Digito-ThrottlingHttpWs_2020-09-21" execution in status "TimedOut"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache default route throttling rate limit as "RateLimit" and burst limit as "BurstLimit" "after" SSM automation execution
      | HttpWsApiGwId                                | HttpWsStageName                                         |
      | {{cfn-output:HTTPWSApiGwTemplate>WsApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>WsStageNameThrottled}} |
    And assert "RateLimit" at "before" became equal to "RateLimit" at "after"
    And assert "BurstLimit" at "before" became equal to "BurstLimit" at "after"