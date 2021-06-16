@api-gw
Feature: SSM automation document Digito-ThrottlingHttpWs_2020-09-21

  Scenario: Execute SSM automation document Digito-ThrottlingHttpWs_2020-09-21 for HTTP API to test failure case
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                | ResourceType |
      | resource_manager/cloud_formation_templates/HTTPWSApiGwTemplate.yml                             | ON_DEMAND    |
      | documents/api-gw/test/throttling-http-ws/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-ThrottlingHttpWs_2020-09-21" SSM document
    And cache default route throttling rate limit as "RateLimit" and burst limit as "BurstLimit" "before" SSM automation execution
      | HttpWsApiGwId                                  | HttpWsStageName                                           |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageNameThrottled}} |

    When SSM automation document "Digito-ThrottlingHttpWs_2020-09-21" executed
      | HttpWsApiGwId                                  | HttpWsStageName                                           | AutomationAssumeRole                                                              | 4xxAlarmName                                             |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageNameThrottled}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoApiGwThrottlingHttpWsAssumeRole}} | {{cfn-output:HTTPWSApiGwTemplate>Http4XXErrorAlarmName}} |
    And Wait for the SSM automation document "Digito-ThrottlingHttpWs_2020-09-21" execution is on step "RollbackCurrentExecution" in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And call endpoint "HttpEndpoint" "12" times with delay "20" seconds using method "POST"
      | HttpEndpoint                                                |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiThrottledEndpoint}} |

    Then SSM automation document "Digito-ThrottlingHttpWs_2020-09-21" execution in status "TimedOut"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache default route throttling rate limit as "RateLimit" and burst limit as "BurstLimit" "after" SSM automation execution
      | HttpWsApiGwId                                  | HttpWsStageName                                           |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageNameThrottled}} |
    And assert "RateLimit" at "before" became equal to "RateLimit" at "after"
    And assert "BurstLimit" at "before" became equal to "BurstLimit" at "after"