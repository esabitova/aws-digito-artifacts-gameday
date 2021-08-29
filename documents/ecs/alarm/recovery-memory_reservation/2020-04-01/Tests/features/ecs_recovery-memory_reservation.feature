@ecs @integration @alarm
Feature: Alarm Setup - ecs HighMemoryReservation
  Scenario: HighMemoryReservation - green
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                    | ResourceType | VPC                      |  PublicSubnetOne                    | PublicSubnetTwo                    |
      | resource_manager/cloud_formation_templates/shared/VPC.yml          | SHARED       |                          |                                     |                                    |
      | resource_manager/cloud_formation_templates/ECSEC2Template.yml      | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>PublicSubnetOne}}  | {{cfn-output:VPC>PublicSubnetTwo}} |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml | SHARED       |                          |                                     |                                    |
    When alarm "ecs:alarm:recovery-memory_reservation:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | ClusterName                               | Threshold  |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:ECSEC2Template>ClusterName}} | 75         |
    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 180 seconds, check every 15 seconds


  Scenario: HighMemoryReservation - red
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                    | ResourceType | VPC                      |  PublicSubnetOne                    | PublicSubnetTwo                    |
      | resource_manager/cloud_formation_templates/shared/VPC.yml          | SHARED       |                          |                                     |                                    |
      | resource_manager/cloud_formation_templates/ECSEC2Template.yml      | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>PublicSubnetOne}}  | {{cfn-output:VPC>PublicSubnetTwo}} |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml | SHARED       |                          |                                     |                                    |
    When alarm "ecs:alarm:recovery-memory_reservation:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | ClusterName                               | Threshold |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:ECSEC2Template>ClusterName}} | 0.01      |
    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes ALARM within 180 seconds, check every 15 seconds


