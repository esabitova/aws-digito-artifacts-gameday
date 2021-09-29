@api-gw
Feature: SSM automation document to change REST API GW usage plan limits

  Scenario: Execute Digito-ChangeRestApiGwQuotaLimitSOP_2020-10-26 to change quota limit with new quota less than 50%
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                               | ResourceType |
      | resource_manager/cloud_formation_templates/RestApiGwTemplate.yml                              | ON_DEMAND    |
      | documents/api-gw/sop/change_quota_limit/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-ChangeRestApiGwQuotaLimitSOP_2020-10-26" SSM document
    And cache API GW property "$.quota.limit" as "QuotaLimit" "before" SSM automation execution
      | RestApiGwUsagePlanId                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} |
    And cache API GW property "$.quota.period" as "QuotaPeriod" "before" SSM automation execution
      | RestApiGwUsagePlanId                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} |
    And register quota settings for teardown
      | UsagePlanId                                           | QuotaLimit                  | QuotaPeriod                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} | {{cache:before>QuotaLimit}} | {{cache:before>QuotaPeriod}} |
    And generate different value of "Limit" than "QuotaLimit" from "49000" to "51000" as "ExpectedQuotaLimit" "before" SSM automation execution
      | QuotaLimit                  |
      | {{cache:before>QuotaLimit}} |

    When SSM automation document "Digito-ChangeRestApiGwQuotaLimitSOP_2020-10-26" executed
      | RestApiGwUsagePlanId                                  | ForceExecution | RestApiGwQuotaLimit                 | RestApiGwQuotaPeriod         | AutomationAssumeRole                                                                        |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} | False          | {{cache:before>ExpectedQuotaLimit}} | {{cache:before>QuotaPeriod}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoChangeRESTAPIGWQuotaLimitSOPAssumeRoleArn}} |

    Then SSM automation document "Digito-ChangeRestApiGwQuotaLimitSOP_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache API GW property "$.quota.limit" as "QuotaLimit" "after" SSM automation execution
      | RestApiGwUsagePlanId                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} |
    And cache API GW property "$.quota.period" as "QuotaPeriod" "after" SSM automation execution
      | RestApiGwUsagePlanId                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} |

    Then assert "ExpectedQuotaLimit" at "before" became equal to "QuotaLimit" at "after"
    And assert "QuotaPeriod" at "before" became equal to "QuotaPeriod" at "after"


  Scenario: Execute Digito-ChangeRestApiGwQuotaLimitSOP_2020-10-26 to change quota limit with new quota more than 50%
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                               | ResourceType |
      | resource_manager/cloud_formation_templates/RestApiGwTemplate.yml                              | ON_DEMAND    |
      | documents/api-gw/sop/change_quota_limit/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-ChangeRestApiGwQuotaLimitSOP_2020-10-26" SSM document
    And cache API GW property "$.quota.limit" as "QuotaLimit" "before" SSM automation execution
      | RestApiGwUsagePlanId                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} |
    And cache API GW property "$.quota.period" as "QuotaPeriod" "before" SSM automation execution
      | RestApiGwUsagePlanId                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} |
    And generate different value of "Limit" than "QuotaLimit" from "500" to "1000" as "ExpectedQuotaLimit" "before" SSM automation execution
      | QuotaLimit                  |
      | {{cache:before>QuotaLimit}} |
    And generate different list value of "Period" than "QuotaPeriod" from "DAY,WEEK,MONTH" as "ExpectedPeriod" "before" SSM automation execution
      | QuotaPeriod                  |
      | {{cache:before>QuotaPeriod}} |

    When SSM automation document "Digito-ChangeRestApiGwQuotaLimitSOP_2020-10-26" executed
      | RestApiGwUsagePlanId                                  | ForceExecution | RestApiGwQuotaLimit                 | RestApiGwQuotaPeriod            | AutomationAssumeRole                                                                        |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} | False          | {{cache:before>ExpectedQuotaLimit}} | {{cache:before>ExpectedPeriod}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoChangeRESTAPIGWQuotaLimitSOPAssumeRoleArn}} |

    Then SSM automation document "Digito-ChangeRestApiGwQuotaLimitSOP_2020-10-26" execution in status "Failed"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache API GW property "$.quota.limit" as "QuotaLimit" "after" SSM automation execution
      | RestApiGwUsagePlanId                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} |
    And cache API GW property "$.quota.period" as "QuotaPeriod" "after" SSM automation execution
      | RestApiGwUsagePlanId                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} |

    Then assert "ExpectedQuotaLimit" at "before" became not equal to "QuotaLimit" at "after"
    And assert "ExpectedPeriod" at "before" became not equal to "QuotaPeriod" at "after"
    And assert "QuotaLimit" at "before" became equal to "QuotaLimit" at "after"
    And assert "QuotaPeriod" at "before" became equal to "QuotaPeriod" at "after"

  Scenario: Execute Digito-ChangeRestApiGwQuotaLimitSOP_2020-10-26 to change quota limit with ForceExecution=True
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                               | ResourceType |
      | resource_manager/cloud_formation_templates/RestApiGwTemplate.yml                              | ON_DEMAND    |
      | documents/api-gw/sop/change_quota_limit/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-ChangeRestApiGwQuotaLimitSOP_2020-10-26" SSM document
    And cache API GW property "$.quota.limit" as "QuotaLimit" "before" SSM automation execution
      | RestApiGwUsagePlanId                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} |
    And cache API GW property "$.quota.period" as "QuotaPeriod" "before" SSM automation execution
      | RestApiGwUsagePlanId                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} |
    And register quota settings for teardown
      | UsagePlanId                                           | QuotaLimit                  | QuotaPeriod                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} | {{cache:before>QuotaLimit}} | {{cache:before>QuotaPeriod}} |
    And generate different value of "Limit" than "QuotaLimit" from "49000" to "51000" as "ExpectedQuotaLimit" "before" SSM automation execution
      | QuotaLimit                  |
      | {{cache:before>QuotaLimit}} |

    When SSM automation document "Digito-ChangeRestApiGwQuotaLimitSOP_2020-10-26" executed
      | RestApiGwUsagePlanId                                  | ForceExecution | RestApiGwQuotaLimit                 | RestApiGwQuotaPeriod         | AutomationAssumeRole                                                                        |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} | False          | {{cache:before>ExpectedQuotaLimit}} | {{cache:before>QuotaPeriod}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoChangeRESTAPIGWQuotaLimitSOPAssumeRoleArn}} |

    Then SSM automation document "Digito-ChangeRestApiGwQuotaLimitSOP_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache API GW property "$.quota.limit" as "QuotaLimit" "after" SSM automation execution
      | RestApiGwUsagePlanId                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} |
    And cache API GW property "$.quota.period" as "QuotaPeriod" "after" SSM automation execution
      | RestApiGwUsagePlanId                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} |

    Then assert "ExpectedQuotaLimit" at "before" became equal to "QuotaLimit" at "after"
    And assert "QuotaPeriod" at "before" became equal to "QuotaPeriod" at "after"
