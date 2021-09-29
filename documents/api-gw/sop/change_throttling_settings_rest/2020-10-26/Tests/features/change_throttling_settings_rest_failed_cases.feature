@api-gw
Feature: SSM automation document to change REST API GW usage plan limits


  Scenario: Change throttling settings for REST API Gateway with ForceExecution=False and new rate limit more than 50%
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                            | ResourceType |
      | resource_manager/cloud_formation_templates/RestApiGwTemplate.yml                                           | ON_DEMAND    |
      | documents/api-gw/sop/change_throttling_settings_rest/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-ChangeRestApiGwThrottlingSettingsSOP_2020-10-26" SSM document
    And cache value of "RestApiGwUsagePlanId" "before" SSM automation execution
      | RestApiGwUsagePlanId                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} |
    And cache usage plan rate limit as "OldRateLimit" and burst limit as "OldBurstLimit" "before" SSM automation execution
    And generate different value of "Limit" than "OldBurstLimit" from "80" to "120" as "ExpectedBurstLimit" "before" SSM automation execution
      | OldBurstLimit                  |
      | {{cache:before>OldBurstLimit}} |

    When SSM automation document "Digito-ChangeRestApiGwThrottlingSettingsSOP_2020-10-26" executed
      | RestApiGwUsagePlanId                                  | RestApiGwThrottlingRate | RestApiGwThrottlingBurst            | AutomationAssumeRole                                                                                |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} | 200                     | {{cache:before>ExpectedBurstLimit}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoChangeRestApiGwThrottlingSettingsSOPAssumeRoleArn}} |
    And SSM automation document "Digito-ChangeRestApiGwThrottlingSettingsSOP_2020-10-26" execution in status "Failed"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache usage plan rate limit as "ActualRateLimit" and burst limit as "ActualBurstLimit" "after" SSM automation execution

    Then assert "OldRateLimit" at "before" became equal to "ActualRateLimit" at "after"
    Then assert "OldBurstLimit" at "before" became equal to "ActualBurstLimit" at "after"


  Scenario: Change throttling settings for REST API Gateway with ForceExecution=False and new burst limit more than 50%
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                            | ResourceType |
      | resource_manager/cloud_formation_templates/RestApiGwTemplate.yml                                           | ON_DEMAND    |
      | documents/api-gw/sop/change_throttling_settings_rest/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-ChangeRestApiGwThrottlingSettingsSOP_2020-10-26" SSM document
    And cache value of "RestApiGwUsagePlanId" "before" SSM automation execution
      | RestApiGwUsagePlanId                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} |
    And cache usage plan rate limit as "OldRateLimit" and burst limit as "OldBurstLimit" "before" SSM automation execution
    And generate different value of "Limit" than "OldRateLimit" from "80" to "120" as "ExpectedRateLimit" "before" SSM automation execution
      | OldRateLimit                  |
      | {{cache:before>OldRateLimit}} |

    When SSM automation document "Digito-ChangeRestApiGwThrottlingSettingsSOP_2020-10-26" executed
      | RestApiGwUsagePlanId                                  | RestApiGwThrottlingRate            | RestApiGwThrottlingBurst | AutomationAssumeRole                                                                                |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} | {{cache:before>ExpectedRateLimit}} | 200                      | {{cfn-output:AutomationAssumeRoleTemplate>DigitoChangeRestApiGwThrottlingSettingsSOPAssumeRoleArn}} |
    And SSM automation document "Digito-ChangeRestApiGwThrottlingSettingsSOP_2020-10-26" execution in status "Failed"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache usage plan rate limit as "ActualRateLimit" and burst limit as "ActualBurstLimit" "after" SSM automation execution

    Then assert "OldRateLimit" at "before" became equal to "ActualRateLimit" at "after"
    Then assert "OldBurstLimit" at "before" became equal to "ActualBurstLimit" at "after"


  Scenario: Change throttling settings for REST API Gateway with ForceExecution=True and new rate limit more than account quota
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                            | ResourceType |
      | resource_manager/cloud_formation_templates/RestApiGwTemplate.yml                                           | ON_DEMAND    |
      | documents/api-gw/sop/change_throttling_settings_rest/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-ChangeRestApiGwThrottlingSettingsSOP_2020-10-26" SSM document
    And cache value of "RestApiGwUsagePlanId" "before" SSM automation execution
      | RestApiGwUsagePlanId                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} |
    And cache usage plan rate limit as "OldRateLimit" and burst limit as "OldBurstLimit" "before" SSM automation execution
    And generate different value of "Limit" than "OldBurstLimit" from "80" to "120" as "ExpectedBurstLimit" "before" SSM automation execution
      | OldBurstLimit                  |
      | {{cache:before>OldBurstLimit}} |

    When SSM automation document "Digito-ChangeRestApiGwThrottlingSettingsSOP_2020-10-26" executed
      | RestApiGwUsagePlanId                                  | RestApiGwThrottlingRate | RestApiGwThrottlingBurst            | ForceExecution | AutomationAssumeRole                                                                                |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} | 20000                   | {{cache:before>ExpectedBurstLimit}} | true           | {{cfn-output:AutomationAssumeRoleTemplate>DigitoChangeRestApiGwThrottlingSettingsSOPAssumeRoleArn}} |
    And SSM automation document "Digito-ChangeRestApiGwThrottlingSettingsSOP_2020-10-26" execution in status "Failed"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache usage plan rate limit as "ActualRateLimit" and burst limit as "ActualBurstLimit" "after" SSM automation execution

    Then assert "OldRateLimit" at "before" became equal to "ActualRateLimit" at "after"
    Then assert "OldBurstLimit" at "before" became equal to "ActualBurstLimit" at "after"


  Scenario: Change throttling settings for REST API Gateway with ForceExecution=True and new burst limit more than account quota
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                            | ResourceType |
      | resource_manager/cloud_formation_templates/RestApiGwTemplate.yml                                           | ON_DEMAND    |
      | documents/api-gw/sop/change_throttling_settings_rest/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-ChangeRestApiGwThrottlingSettingsSOP_2020-10-26" SSM document
    And cache value of "RestApiGwUsagePlanId" "before" SSM automation execution
      | RestApiGwUsagePlanId                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} |
    And cache usage plan rate limit as "OldRateLimit" and burst limit as "OldBurstLimit" "before" SSM automation execution
    And generate different value of "Limit" than "OldRateLimit" from "80" to "120" as "ExpectedRateLimit" "before" SSM automation execution
      | OldRateLimit                  |
      | {{cache:before>OldRateLimit}} |

    When SSM automation document "Digito-ChangeRestApiGwThrottlingSettingsSOP_2020-10-26" executed
      | RestApiGwUsagePlanId                                  | RestApiGwThrottlingRate            | RestApiGwThrottlingBurst | ForceExecution | AutomationAssumeRole                                                                                |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} | {{cache:before>ExpectedRateLimit}} | 10000                    | true           | {{cfn-output:AutomationAssumeRoleTemplate>DigitoChangeRestApiGwThrottlingSettingsSOPAssumeRoleArn}} |
    And SSM automation document "Digito-ChangeRestApiGwThrottlingSettingsSOP_2020-10-26" execution in status "Failed"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache usage plan rate limit as "ActualRateLimit" and burst limit as "ActualBurstLimit" "after" SSM automation execution

    Then assert "OldRateLimit" at "before" became equal to "ActualRateLimit" at "after"
    Then assert "OldBurstLimit" at "before" became equal to "ActualBurstLimit" at "after"
