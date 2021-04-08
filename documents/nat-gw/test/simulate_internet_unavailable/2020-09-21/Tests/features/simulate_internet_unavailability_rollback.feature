@natgw
Feature: SSM automation document to simulate internet unavalability through changing route to NAT GW

    Scenario: Simulate rollback after test execution
        Given the cloud formation templates as integration test resources
            | CfnTemplatePath                                                                                           | ResourceType |
            | resource_manager/cloud_formation_templates/NatCfnTemplate.yml                                             | ON_DEMAND    |
            | documents/nat-gw/test/simulate_internet_unavailable/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
        And trigger lambda {{cfn-output:NatCfnTemplate>LambdaArn}} asynchronously
        # And Wait until alarm {{cfn-output:NatCfnTemplate>BytesOutToSourceAlarm}} becomes OK within 300 seconds, check every 15 seconds
        When SSM automation document "Digito-SimulateInternetUnavailable_2020-09-21" executed
            | NatGatewayId                               | SyntheticAlarmName                                  | AutomationAssumeRole                                                                    |
            | {{cfn-output:NatCfnTemplate>NatGatewayId}} | {{cfn-output:NatCfnTemplate>BytesOutToSourceAlarm}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoSimulateInternetUnavailableAssumeRole}} |
        Then Wait for the SSM automation document "Digito-SimulateInternetUnavailable_2020-09-21" execution is on step "AssertAlarmToBeRed" in status "InProgress" for "600" seconds
            | ExecutionId                |
            | {{cache:SsmExecutionId>1}} |
        And terminate "Digito-SimulateInternetUnavailable_2020-09-21" SSM automation document
            | ExecutionId                |
            | {{cache:SsmExecutionId>1}} |

        # Rollback
        When SSM automation document "Digito-SimulateInternetUnavailable_2020-09-21" executed
            | NatGatewayId                               | IsRollback | PreviousExecutionId        | SyntheticAlarmName                                  | AutomationAssumeRole                                                                    |
            | {{cfn-output:NatCfnTemplate>NatGatewayId}} | true       | {{cache:SsmExecutionId>1}} | {{cfn-output:NatCfnTemplate>BytesOutToSourceAlarm}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoSimulateInternetUnavailableAssumeRole}} |
        Then Wait for the SSM automation document "Digito-SimulateInternetUnavailable_2020-09-21" execution is on step "GetPreviousExecutionInputsNatGw" in status "Success" for "600" seconds
            | ExecutionId                |
            | {{cache:SsmExecutionId>2}} |
        And Wait for the SSM automation document "Digito-SimulateInternetUnavailable_2020-09-21" execution is on step "AssertNatGatewayId" in status "Success" for "600" seconds
            | ExecutionId                |
            | {{cache:SsmExecutionId>2}} |
        And Wait for the SSM automation document "Digito-SimulateInternetUnavailable_2020-09-21" execution is on step "GetPreviousExecutionInputsSubnet" in status "Success" for "600" seconds
            | ExecutionId                |
            | {{cache:SsmExecutionId>2}} |
        And Wait for the SSM automation document "Digito-SimulateInternetUnavailable_2020-09-21" execution is on step "AssertPrivateSubnetId" in status "Success" for "600" seconds
            | ExecutionId                |
            | {{cache:SsmExecutionId>2}} |
        And Wait for the SSM automation document "Digito-SimulateInternetUnavailable_2020-09-21" execution is on step "GetPreviousExecutionBackupOutputs" in status "Success" for "600" seconds
            | ExecutionId                |
            | {{cache:SsmExecutionId>2}} |
        And Wait for the SSM automation document "Digito-SimulateInternetUnavailable_2020-09-21" execution is on step "RollbackPreviousExecution" in status "Success" for "600" seconds
            | ExecutionId                |
            | {{cache:SsmExecutionId>2}} |