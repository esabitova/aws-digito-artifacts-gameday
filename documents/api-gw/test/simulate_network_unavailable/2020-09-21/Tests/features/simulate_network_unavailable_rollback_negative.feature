@api-gw
Feature: SSM automation document Digito-RestApiGwSimulateNetworkUnavailable_2020-09-21

  Scenario: Execute SSM automation document Digito-RestApiGwSimulateNetworkUnavailable_2020-09-21 to test rollback failure when inputs different than original execution
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                          | ResourceType |
      | resource_manager/cloud_formation_templates/RestApiGwPrivateEndpointTemplate.yml                          | ON_DEMAND    |
      | documents/api-gw/test/simulate_network_unavailable/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestApiGwSimulateNetworkUnavailable_2020-09-21" SSM document
    And cache value of "ApiKeyId,LambdaArn" "before" SSM automation execution
      | ApiKeyId                                                 | LambdaArn                                                 |
      | {{cfn-output:RestApiGwPrivateEndpointTemplate>ApiKeyId}} | {{cfn-output:RestApiGwPrivateEndpointTemplate>LambdaArn}} |
    And get API key "ApiKeyId" and invoke lambda "LambdaArn" to perform "60" http requests with interval "10" seconds

    When SSM automation document "Digito-RestApiGwSimulateNetworkUnavailable_2020-09-21" executed
      | RestApiGwId                                                 | SecurityGroupIdListToUnassign                                   | AutomationAssumeRole                                                                        | ApiGwCountAlarmName                                            |
      | {{cfn-output:RestApiGwPrivateEndpointTemplate>RestApiGwId}} | {{cfn-output:RestApiGwPrivateEndpointTemplate>SecurityGroupId}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoApiGwSimulateNetworkUnavailableAssumeRole}} | {{cfn-output:RestApiGwPrivateEndpointTemplate>CountAlarmName}} |

    Then Wait for the SSM automation document "Digito-RestApiGwSimulateNetworkUnavailable_2020-09-21" execution is on step "InjectFailure" in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And terminate "Digito-RestApiGwSimulateNetworkUnavailable_2020-09-21" SSM automation document
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And Wait for the SSM automation document "Digito-RestApiGwSimulateNetworkUnavailable_2020-09-21" execution is on step "TriggerRollback" in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And SSM automation document "Digito-RestApiGwSimulateNetworkUnavailable_2020-09-21" execution in status "Cancelled"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    # We are using a different set of inputs from original execution. We use WrongRestApiGwId as a value of RestApiGwId input parameter.
    Then SSM automation document "Digito-RestApiGwSimulateNetworkUnavailable_2020-09-21" executed
      | RestApiGwId      | IsRollback | PreviousExecutionId        | AutomationAssumeRole                                                                        | ApiGwCountAlarmName                                            |
      | WrongRestApiGwId | True       | {{cache:SsmExecutionId>1}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoApiGwSimulateNetworkUnavailableAssumeRole}} | {{cfn-output:RestApiGwPrivateEndpointTemplate>CountAlarmName}} |
    And SSM automation document "Digito-RestApiGwSimulateNetworkUnavailable_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>2}} |

    Then assert "CheckIsRollback,GetInputsFromPreviousExecution,AssertInputsFromPreviousExecution" steps are successfully executed in order
      | ExecutionId                |
      | {{cache:SsmExecutionId>2}} |
    And assert "CheckIsRollback,AssertAlarmToBeGreenBeforeTest,BackupCurrentExecution,InjectFailure,TriggerRollback" steps are successfully executed in order
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

