@natgw @integration @alarm
Feature: Alarm Setup - NatGW ErrorPortAllocation
  Scenario: Check alarm for number of times the NAT gateway could not allocate a source port
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                    | ResourceType |
      | resource_manager/cloud_formation_templates/NatCfnTemplate.yml      | ON_DEMAND    |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml | SHARED       |

    When alarm "nat-gw:alarm:error_port_allocation:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | NatGatewayId                               | Threshold |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:NatCfnTemplate>NatGatewayId}} | 0         |
    And trigger lambda "{{cfn-output:NatCfnTemplate>LambdaArn}}" asynchronously
    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 180 seconds, check every 15 seconds