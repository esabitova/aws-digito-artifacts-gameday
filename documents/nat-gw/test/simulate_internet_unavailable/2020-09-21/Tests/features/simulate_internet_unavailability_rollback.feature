@natgw
Feature: SSM automation document to simulate internet unavalability through changing route to NAT GW

    Scenario: Simulate rollback after test execution
        Given the cloud formation templates as integration test resources
            | CfnTemplatePath                                                                                           | ResourceType |
            | resource_manager/cloud_formation_templates/NatCfnTemplate.yml                                             | DEDICATED    |
            | documents/nat-gw/test/simulate_internet_unavailable/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
        And published "Digito-SimulateInternetUnavailable_2020-09-21" SSM document
        And trigger lambda "{{cfn-output:NatCfnTemplate>LambdaArn}}" asynchronously
        And Wait until alarm {{cfn-output:NatCfnTemplate>BytesOutToSourceAlarm}} becomes OK within 600 seconds, check every 15 seconds
        When SSM automation document "Digito-SimulateInternetUnavailable_2020-09-21" executed
            | NatGatewayId                               | BytesOutToSourceAlarm                               | AutomationAssumeRole                                                                    |
            | {{cfn-output:NatCfnTemplate>NatGatewayId}} | {{cfn-output:NatCfnTemplate>BytesOutToSourceAlarm}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoSimulateInternetUnavailableAssumeRole}} |
        Then Wait for the SSM automation document "Digito-SimulateInternetUnavailable_2020-09-21" execution is on step "AssertAlarmToBeRed" in status "InProgress"
            | ExecutionId                |
            | {{cache:SsmExecutionId>1}} |
        And terminate "Digito-SimulateInternetUnavailable_2020-09-21" SSM automation document
            | ExecutionId                |
            | {{cache:SsmExecutionId>1}} |

        Then Wait for the SSM automation document "Digito-SimulateInternetUnavailable_2020-09-21" execution is on step "TriggerRollback" in status "Success"
            |ExecutionId               |
            |{{cache:SsmExecutionId>1}}|

        Then SSM automation document "Digito-SimulateInternetUnavailable_2020-09-21" execution in status "Cancelled"
            |ExecutionId               |
            |{{cache:SsmExecutionId>1}}|

        Then cache rollback execution id
            |ExecutionId               |
            |{{cache:SsmExecutionId>1}}|

        # Rollback verification
        Then Wait for the SSM automation document "Digito-SimulateInternetUnavailable_2020-09-21" execution is on step "GetPreviousExecutionInputsNatGw" in status "Success"
            | ExecutionId                |
            | {{cache:SsmExecutionId>2}} |
        And Wait for the SSM automation document "Digito-SimulateInternetUnavailable_2020-09-21" execution is on step "AssertNatGatewayId" in status "Success"
            | ExecutionId                |
            | {{cache:SsmExecutionId>2}} |
        And Wait for the SSM automation document "Digito-SimulateInternetUnavailable_2020-09-21" execution is on step "GetPreviousExecutionInputsSubnet" in status "Success"
            | ExecutionId                |
            | {{cache:SsmExecutionId>2}} |
        And Wait for the SSM automation document "Digito-SimulateInternetUnavailable_2020-09-21" execution is on step "AssertPrivateSubnetId" in status "Success"
            | ExecutionId                |
            | {{cache:SsmExecutionId>2}} |
        And Wait for the SSM automation document "Digito-SimulateInternetUnavailable_2020-09-21" execution is on step "GetPreviousExecutionBackupOutputs" in status "Success"
            | ExecutionId                |
            | {{cache:SsmExecutionId>2}} |
        And Wait for the SSM automation document "Digito-SimulateInternetUnavailable_2020-09-21" execution is on step "RollbackPreviousExecution" in status "Success"
            | ExecutionId                |
            | {{cache:SsmExecutionId>2}} |