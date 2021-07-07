@natgw @integration @alarm
Feature: Alarm Setup - NatGW ConnectionAttemptCount
  Scenario: Check alarm for number of connection attempts for which there was no response
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                    | ResourceType |
      | resource_manager/cloud_formation_templates/NatCfnTemplate.yml      | ON_DEMAND    |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml | SHARED       |

    When alarm "nat-gw:alarm:connection_attempt_count:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | NatGatewayId                               |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:NatCfnTemplate>NatGatewayId}} |
    And trigger lambda "{{cfn-output:NatCfnTemplate>LambdaArn}}" asynchronously
    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 180 seconds, check every 15 seconds