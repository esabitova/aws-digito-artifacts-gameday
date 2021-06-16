@api-gw
Feature: SSM automation document Digito-RestApiGwThrottling_2020-09-21

  Scenario: Execute SSM automation document Digito-RestApiGwThrottling_2020-09-21 in negative rollback test with wrong Usage Plan ID
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                             | ResourceType |
      | resource_manager/cloud_formation_templates/RestApiGwTemplate.yml                            | ON_DEMAND    |
      | documents/api-gw/test/throttling-rest/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestApiGwThrottling_2020-09-21" SSM document

    When SSM automation document "Digito-RestApiGwThrottling_2020-09-21" executed
      | RestApiGwUsagePlanId                                  | AutomationAssumeRole                                                            | ApiGw4xxAlarmName                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestApiGwThrottlingAssumeRole}} | {{cfn-output:RestApiGwTemplate>4XXErrorAlarmName}} |

    Then Wait for the SSM automation document "Digito-RestApiGwThrottling_2020-09-21" execution is on step "BackupThrottlingConfiguration" in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And terminate "Digito-RestApiGwThrottling_2020-09-21" SSM automation document
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    Then SSM automation document "Digito-RestApiGwThrottling_2020-09-21" executed
      | RestApiGwUsagePlanId | IsRollback | PreviousExecutionId        | AutomationAssumeRole                                                            | ApiGw4xxAlarmName                                  |
      | WrongUsagePlanID     | true       | {{cache:SsmExecutionId>1}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestApiGwThrottlingAssumeRole}} | {{cfn-output:RestApiGwTemplate>4XXErrorAlarmName}} |
    And SSM automation document "Digito-RestApiGwThrottling_2020-09-21" execution in status "Failed"
      | ExecutionId                |
      | {{cache:SsmExecutionId>2}} |

    Then assert SSM automation document step "AssertInputsFromPreviousExecution" execution in status "Failed"
      | ExecutionId                |
      | {{cache:SsmExecutionId>2}} |
    And assert "CheckIsRollback,GetInputsFromPreviousExecution" steps are successfully executed in order
      | ExecutionId                |
      | {{cache:SsmExecutionId>2}} |


  Scenario: Execute SSM automation document Digito-RestApiGwThrottling_2020-09-21 in negative rollback test with wrong Stage Name
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                             | ResourceType |
      | resource_manager/cloud_formation_templates/RestApiGwTemplate.yml                            | ON_DEMAND    |
      | documents/api-gw/test/throttling-rest/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestApiGwThrottling_2020-09-21" SSM document

    When SSM automation document "Digito-RestApiGwThrottling_2020-09-21" executed
      | RestApiGwUsagePlanId                                  | RestApiGwStageName                                  | RestApiGwId                                  | AutomationAssumeRole                                                            | ApiGw4xxAlarmName                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} | {{cfn-output:RestApiGwTemplate>RestApiGwStageName}} | {{cfn-output:RestApiGwTemplate>RestApiGwId}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestApiGwThrottlingAssumeRole}} | {{cfn-output:RestApiGwTemplate>4XXErrorAlarmName}} |

    Then Wait for the SSM automation document "Digito-RestApiGwThrottling_2020-09-21" execution is on step "BackupThrottlingConfiguration" in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And terminate "Digito-RestApiGwThrottling_2020-09-21" SSM automation document
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    Then SSM automation document "Digito-RestApiGwThrottling_2020-09-21" executed
      | RestApiGwUsagePlanId                                  | RestApiGwStageName | RestApiGwId                                  | IsRollback | PreviousExecutionId        | AutomationAssumeRole                                                            | ApiGw4xxAlarmName                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} | WrongStageName     | {{cfn-output:RestApiGwTemplate>RestApiGwId}} | true       | {{cache:SsmExecutionId>1}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestApiGwThrottlingAssumeRole}} | {{cfn-output:RestApiGwTemplate>4XXErrorAlarmName}} |
    And SSM automation document "Digito-RestApiGwThrottling_2020-09-21" execution in status "Failed"
      | ExecutionId                |
      | {{cache:SsmExecutionId>2}} |

    Then assert SSM automation document step "AssertInputsFromPreviousExecution" execution in status "Failed"
      | ExecutionId                |
      | {{cache:SsmExecutionId>2}} |
    And assert "CheckIsRollback,GetInputsFromPreviousExecution" steps are successfully executed in order
      | ExecutionId                |
      | {{cache:SsmExecutionId>2}} |

  Scenario: Execute SSM automation document Digito-RestApiGwThrottling_2020-09-21 in negative rollback test with wrong API Gateway ID
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                             | ResourceType |
      | resource_manager/cloud_formation_templates/RestApiGwTemplate.yml                            | ON_DEMAND    |
      | documents/api-gw/test/throttling-rest/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestApiGwThrottling_2020-09-21" SSM document

    When SSM automation document "Digito-RestApiGwThrottling_2020-09-21" executed
      | RestApiGwUsagePlanId                                  | RestApiGwStageName                                  | RestApiGwId                                  | AutomationAssumeRole                                                            | ApiGw4xxAlarmName                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} | {{cfn-output:RestApiGwTemplate>RestApiGwStageName}} | {{cfn-output:RestApiGwTemplate>RestApiGwId}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestApiGwThrottlingAssumeRole}} | {{cfn-output:RestApiGwTemplate>4XXErrorAlarmName}} |

    Then Wait for the SSM automation document "Digito-RestApiGwThrottling_2020-09-21" execution is on step "BackupThrottlingConfiguration" in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And terminate "Digito-RestApiGwThrottling_2020-09-21" SSM automation document
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    Then SSM automation document "Digito-RestApiGwThrottling_2020-09-21" executed
      | RestApiGwUsagePlanId                                  | RestApiGwStageName                                  | RestApiGwId      | IsRollback | PreviousExecutionId        | AutomationAssumeRole                                                            | ApiGw4xxAlarmName                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwUsagePlanId}} | {{cfn-output:RestApiGwTemplate>RestApiGwStageName}} | WrongRestApiGwId | true       | {{cache:SsmExecutionId>1}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestApiGwThrottlingAssumeRole}} | {{cfn-output:RestApiGwTemplate>4XXErrorAlarmName}} |
    And SSM automation document "Digito-RestApiGwThrottling_2020-09-21" execution in status "Failed"
      | ExecutionId                |
      | {{cache:SsmExecutionId>2}} |

    Then assert SSM automation document step "AssertInputsFromPreviousExecution" execution in status "Failed"
      | ExecutionId                |
      | {{cache:SsmExecutionId>2}} |
    And assert "CheckIsRollback,GetInputsFromPreviousExecution" steps are successfully executed in order
      | ExecutionId                |
      | {{cache:SsmExecutionId>2}} |