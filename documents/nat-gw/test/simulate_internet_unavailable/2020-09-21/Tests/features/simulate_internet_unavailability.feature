@natgw
Feature: SSM automation document to simulate internet unavalability through changing route to NAT GW

  Scenario: Simulate internet unavalability through changing route to NAT GW when customer specified only NatGatewayId
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                           | ResourceType |
      | resource_manager/cloud_formation_templates/NatCfnTemplate.yml                                             | DEDICATED    |
      | documents/nat-gw/test/simulate_internet_unavailable/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-SimulateNatGwInternetUnavailableTest_2020-09-21" SSM document
    And trigger lambda "{{cfn-output:NatCfnTemplate>LambdaArn}}" asynchronously
    And Wait until alarm {{cfn-output:NatCfnTemplate>BytesOutToSourceAlarmName}} becomes OK within 600 seconds, check every 15 seconds
    When SSM automation document "Digito-SimulateNatGwInternetUnavailableTest_2020-09-21" executed
      | NatGatewayId                               | BytesOutToSourceAlarmName                               | AutomationAssumeRole                                                                             |
      | {{cfn-output:NatCfnTemplate>NatGatewayId}} | {{cfn-output:NatCfnTemplate>BytesOutToSourceAlarmName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoSimulateNatGwInternetUnavailableTestAssumeRole}} |
    Then SSM automation document "Digito-SimulateNatGwInternetUnavailableTest_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |