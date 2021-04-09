@natgw
Feature: SSM automation document to simulate internet unavalability through changing route to NAT GW

  Scenario: Simulate internet unavalability through changing route to NAT GW when customer specified only NatGatewayId
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                           | ResourceType |
      | resource_manager/cloud_formation_templates/NatCfnTemplate.yml                                             | ON_DEMAND    |
      | documents/nat-gw/test/simulate_internet_unavailable/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-SimulateInternetUnavailable_2020-09-21" SSM document
    And trigger lambda "{{cfn-output:NatCfnTemplate>LambdaArn}}" asynchronously
    And Wait until alarm {{cfn-output:NatCfnTemplate>BytesOutToSourceAlarm}} becomes OK within 300 seconds, check every 15 seconds
    When SSM automation document "Digito-SimulateInternetUnavailable_2020-09-21" executed
      | NatGatewayId                               | SyntheticAlarmName                                  | AutomationAssumeRole                                                                    |
      | {{cfn-output:NatCfnTemplate>NatGatewayId}} | {{cfn-output:NatCfnTemplate>BytesOutToSourceAlarm}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoSimulateInternetUnavailableAssumeRole}} |
    Then SSM automation document "Digito-SimulateInternetUnavailable_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |