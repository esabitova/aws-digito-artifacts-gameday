@app_common @integration
Feature: SSM automation document Digito-AppCommonRecoverCrossRegion_2021-04-01
  Scenario: Execute SSM automation document Digito-AppCommonRecoverCrossRegion_2021-04-01
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                     | ResourceType |
      | documents/app_common/sop/recover_cross_region/2021-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-AppCommonRecoverCrossRegion_2021-04-01" SSM document

    When SSM automation document "Digito-AppCommonRecoverCrossRegion_2021-04-01" executed
      | AutomationAssumeRole                                                             |
      | {{cfn-output:AutomationAssumeRoleTemplate>DigitoAppCommonCrossRegionRecoveryAssumeRole}} |

    Then Wait for the SSM automation document "Digito-AppCommonRecoverCrossRegion_2021-04-01" execution is on step "FenceSourceRegion_Describe" in status "Waiting"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And SSM Automation Resume for execution "{{cache:SsmExecutionId>1}}" on step "FenceSourceRegion_Describe"

    Then Wait for the SSM automation document "Digito-AppCommonRecoverCrossRegion_2021-04-01" execution is on step "RecoverState_Describe" in status "Waiting"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And SSM Automation Resume for execution "{{cache:SsmExecutionId>1}}" on step "RecoverState_Describe"

    Then Wait for the SSM automation document "Digito-AppCommonRecoverCrossRegion_2021-04-01" execution is on step "ScaleUpComponents_Describe" in status "Waiting"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And SSM Automation Resume for execution "{{cache:SsmExecutionId>1}}" on step "ScaleUpComponents_Describe"


    Then Wait for the SSM automation document "Digito-AppCommonRecoverCrossRegion_2021-04-01" execution is on step "UpdateGlobalServices_Describe" in status "Waiting"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And SSM Automation Resume for execution "{{cache:SsmExecutionId>1}}" on step "UpdateGlobalServices_Describe"


    Then Wait for the SSM automation document "Digito-AppCommonRecoverCrossRegion_2021-04-01" execution is on step "Verification_Describe" in status "Waiting"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And SSM Automation Resume for execution "{{cache:SsmExecutionId>1}}" on step "Verification_Describe"


    Then SSM automation document "Digito-AppCommonRecoverCrossRegion_2021-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
