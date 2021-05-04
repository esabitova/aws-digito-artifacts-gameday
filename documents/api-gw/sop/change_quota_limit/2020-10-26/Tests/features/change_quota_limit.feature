@api-gw
Feature: SSM automation document to change REST API GW usage plan limits

  Scenario: Change REST API GW usage plan limits with ForceExecution=False and new quota is not more than 50%
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                               | ResourceType |
      | resource_manager/cloud_formation_templates/RestApiGwTemplate.yml                              | ON_DEMAND    |
      | documents/api-gw/sop/change_quota_limit/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestApiGwChangeQuotaLimit_2020-10-26" SSM document
    And cache API GW property "$.quota.limit" as "OldLimit" "before" SSM automation execution
      | RestApiGwUsagePlanId                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} |
    And cache API GW property "$.quota.period" as "OldPeriod" "before" SSM automation execution
      | RestApiGwUsagePlanId                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} |
    And generate different value of "Limit" than "OldLimit" from "49000" to "51000" as "ExpectedLimit" "before" SSM automation execution
      | OldLimit                  |
      | {{cache:before>OldLimit}} |
    And SSM automation document "Digito-RestApiGwChangeQuotaLimit_2020-10-26" executed
      | RestApiGwUsagePlanId                                  | ForceExecution | RestApiGwQuotaLimit            | RestApiGwQuotaPeriod       | AutomationAssumeRole                                                                     |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} | False          | {{cache:before>ExpectedLimit}} | {{cache:before>OldPeriod}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRESTAPIGWChangeQuotaLimitAssumeRoleArn}} |
    When SSM automation document "Digito-RestApiGwChangeQuotaLimit_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache API GW property "$.quota.limit" as "ActualLimit" "after" SSM automation execution
      | RestApiGwUsagePlanId                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} |
    And cache API GW property "$.quota.period" as "ActualPeriod" "after" SSM automation execution
      | RestApiGwUsagePlanId                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} |
    Then assert "ExpectedLimit" at "before" became equal to "ActualLimit" at "after"
    And assert "OldPeriod" at "before" became equal to "ActualPeriod" at "after"


  Scenario: Change REST API GW usage plan limits with ForceExecution=False and new quota is more than 50%
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                               | ResourceType |
      | resource_manager/cloud_formation_templates/RestApiGwTemplate.yml                              | ON_DEMAND    |
      | documents/api-gw/sop/change_quota_limit/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestApiGwChangeQuotaLimit_2020-10-26" SSM document
    And cache API GW property "$.quota.limit" as "OldLimit" "before" SSM automation execution
      | RestApiGwUsagePlanId                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} |
    And cache API GW property "$.quota.period" as "OldPeriod" "before" SSM automation execution
      | RestApiGwUsagePlanId                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} |
    And generate different value of "Limit" than "OldLimit" from "500" to "1000" as "ExpectedLimit" "before" SSM automation execution
      | OldLimit                  |
      | {{cache:before>OldLimit}} |
    And generate different list value of "Period" than "OldPeriod" from "DAY,WEEK,MONTH" as "ExpectedPeriod" "before" SSM automation execution
      | OldPeriod                  |
      | {{cache:before>OldPeriod}} |
    And SSM automation document "Digito-RestApiGwChangeQuotaLimit_2020-10-26" executed
      | RestApiGwUsagePlanId                                  | ForceExecution | RestApiGwQuotaLimit            | RestApiGwQuotaPeriod            | AutomationAssumeRole                                                                     |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} | False          | {{cache:before>ExpectedLimit}} | {{cache:before>ExpectedPeriod}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRESTAPIGWChangeQuotaLimitAssumeRoleArn}} |
    When SSM automation document "Digito-RestApiGwChangeQuotaLimit_2020-10-26" execution in status "Failed"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache API GW property "$.quota.limit" as "ActualLimit" "after" SSM automation execution
      | RestApiGwUsagePlanId                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} |
    And cache API GW property "$.quota.period" as "ActualPeriod" "after" SSM automation execution
      | RestApiGwUsagePlanId                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} |
    Then assert "ExpectedLimit" at "before" became not equal to "ActualLimit" at "after"
    And assert "ExpectedPeriod" at "before" became not equal to "ActualPeriod" at "after"
    And assert "OldLimit" at "before" became equal to "ActualLimit" at "after"
    And assert "OldPeriod" at "before" became equal to "ActualPeriod" at "after"

  Scenario: Change REST API GW usage plan limits with ForceExecution=True
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                               | ResourceType |
      | resource_manager/cloud_formation_templates/RestApiGwTemplate.yml                              | ON_DEMAND    |
      | documents/api-gw/sop/change_quota_limit/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestApiGwChangeQuotaLimit_2020-10-26" SSM document
    And cache API GW property "$.quota.limit" as "OldLimit" "before" SSM automation execution
      | RestApiGwUsagePlanId                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} |
    And cache API GW property "$.quota.period" as "OldPeriod" "before" SSM automation execution
      | RestApiGwUsagePlanId                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} |
    And generate different value of "Limit" than "OldLimit" from "49000" to "51000" as "ExpectedLimit" "before" SSM automation execution
      | OldLimit                  |
      | {{cache:before>OldLimit}} |
    And SSM automation document "Digito-RestApiGwChangeQuotaLimit_2020-10-26" executed
      | RestApiGwUsagePlanId                                  | ForceExecution | RestApiGwQuotaLimit            | RestApiGwQuotaPeriod       | AutomationAssumeRole                                                                     |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} | False          | {{cache:before>ExpectedLimit}} | {{cache:before>OldPeriod}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRESTAPIGWChangeQuotaLimitAssumeRoleArn}} |
    When SSM automation document "Digito-RestApiGwChangeQuotaLimit_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache API GW property "$.quota.limit" as "ActualLimit" "after" SSM automation execution
      | RestApiGwUsagePlanId                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} |
    And cache API GW property "$.quota.period" as "ActualPeriod" "after" SSM automation execution
      | RestApiGwUsagePlanId                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} |
    Then assert "ExpectedLimit" at "before" became equal to "ActualLimit" at "after"
    And assert "OldPeriod" at "before" became equal to "ActualPeriod" at "after"
