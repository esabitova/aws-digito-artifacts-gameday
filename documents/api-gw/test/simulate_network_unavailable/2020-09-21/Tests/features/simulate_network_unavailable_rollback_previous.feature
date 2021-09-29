@api-gw
Feature: SSM automation document Digito-SimulateRestApiGwNetworkUnavailableTest_2020-09-21

  Scenario: Execute SSM automation document Digito-SimulateRestApiGwNetworkUnavailableTest_2020-09-21 in rollback test
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                          | ResourceType |
      | resource_manager/cloud_formation_templates/RestApiGwPrivateEndpointTemplate.yml                          | ON_DEMAND    |
      | documents/api-gw/test/simulate_network_unavailable/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-SimulateRestApiGwNetworkUnavailableTest_2020-09-21" SSM document
    And cache value of "ApiKeyId,LambdaArn,RestApiGwId" "before" SSM automation execution
      | ApiKeyId                                                 | LambdaArn                                                 | RestApiGwId                                                 |
      | {{cfn-output:RestApiGwPrivateEndpointTemplate>ApiKeyId}} | {{cfn-output:RestApiGwPrivateEndpointTemplate>LambdaArn}} | {{cfn-output:RestApiGwPrivateEndpointTemplate>RestApiGwId}} |
    And get REST API Gateway endpoints and their security groups, cache map as "VpcEndpointSecurityGroupsMap" "before" SSM automation execution
    And get API key "ApiKeyId" and invoke lambda "LambdaArn" to perform "60" http requests with interval "10" seconds


    When SSM automation document "Digito-SimulateRestApiGwNetworkUnavailableTest_2020-09-21" executed
      | RestApiGwId                                                 | AutomationAssumeRole                                                                                | ApiGwCountAlarmName                                            |
      | {{cfn-output:RestApiGwPrivateEndpointTemplate>RestApiGwId}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoSimulateRestApiGwNetworkUnavailableTestAssumeRole}} | {{cfn-output:RestApiGwPrivateEndpointTemplate>CountAlarmName}} |

    Then Wait for the SSM automation document "Digito-SimulateRestApiGwNetworkUnavailableTest_2020-09-21" execution is on step "AssertAlarmToBeRed" in status "InProgress"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And terminate "Digito-SimulateRestApiGwNetworkUnavailableTest_2020-09-21" SSM automation document
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    Then Wait for the SSM automation document "Digito-SimulateRestApiGwNetworkUnavailableTest_2020-09-21" execution is on step "TriggerRollback" in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And SSM automation document "Digito-SimulateRestApiGwNetworkUnavailableTest_2020-09-21" execution in status "Cancelled"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache rollback execution id
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    Then SSM automation document "Digito-SimulateRestApiGwNetworkUnavailableTest_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>2}} |
    And assert SSM automation document step "RollbackPreviousExecution" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>2}} |
    And get REST API Gateway endpoints and their security groups, cache map as "VpcEndpointSecurityGroupsMap" "after" SSM automation execution

    Then assert "VpcEndpointSecurityGroupsMap" at "before" became equal to "VpcEndpointSecurityGroupsMap" at "after"
    And assert "CheckIsRollback,AssertAlarmToBeGreenBeforeTest,BackupCurrentExecution,InjectFailure,TriggerRollback" steps are successfully executed in order
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And assert "CheckIsRollback,GetInputsFromPreviousExecution,AssertInputsFromPreviousExecution,PrepareRollbackOfPreviousExecution,RollbackPreviousExecution" steps are successfully executed in order
      | ExecutionId                |
      | {{cache:SsmExecutionId>2}} |
