@natgw @integration @alarm
Feature: Alarm Setup - NatGW IdleTimeoutCount
  Scenario: Check alarm for number of connections that transitioned from the active state to the idle state
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                    | ResourceType |
      | resource_manager/cloud_formation_templates/NatCfnTemplate.yml      | ON_DEMAND    |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml | SHARED       |

    When alarm "nat-gw:alarm:idle_timeout_count:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | NatGatewayId                               | Threshold |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:NatCfnTemplate>NatGatewayId}} | 0         |
    And trigger lambda "{{cfn-output:NatCfnTemplate>LambdaArn}}" asynchronously
    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 180 seconds, check every 15 seconds