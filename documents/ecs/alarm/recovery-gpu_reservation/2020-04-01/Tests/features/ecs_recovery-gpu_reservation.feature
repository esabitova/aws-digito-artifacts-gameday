@ecs @integration @alarm
Feature: Alarm Setup - ecs HighGPUReservation
  Scenario: HighGPUReservation - green
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                    | ResourceType | VPC                      |  PublicSubnetOne                    | PublicSubnetTwo                    | IsGPUTask | InstanceType  | ECSAMI                                                                  |
      | resource_manager/cloud_formation_templates/shared/VPC.yml          | SHARED       |                          |                                     |                                    |           |               |                                                                         |
      | resource_manager/cloud_formation_templates/ECSEC2Template.yml      | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>PublicSubnetOne}}  | {{cfn-output:VPC>PublicSubnetTwo}} | true      | g3s.xlarge    | /aws/service/ecs/optimized-ami/amazon-linux-2/gpu/recommended/image_id  |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml | SHARED       |                          |                                     |                                    |           |               |                                                                         |
    When alarm "ecs:alarm:recovery-gpu_reservation:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | ClusterName                               | Threshold  |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:ECSEC2Template>ClusterName}} | 120         |
    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 180 seconds, check every 15 seconds


  Scenario: HighGPUReservation - red
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                    | ResourceType | VPC                      |  PublicSubnetOne                    | PublicSubnetTwo                    | IsGPUTask | InstanceType  | ECSAMI                                                                  |
      | resource_manager/cloud_formation_templates/shared/VPC.yml          | SHARED       |                          |                                     |                                    |           |               |                                                                         |
      | resource_manager/cloud_formation_templates/ECSEC2Template.yml      | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>PublicSubnetOne}}  | {{cfn-output:VPC>PublicSubnetTwo}} | true      | g3s.xlarge    | /aws/service/ecs/optimized-ami/amazon-linux-2/gpu/recommended/image_id  |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml | SHARED       |                          |                                     |                                    |           |               |                                                                         |
    When alarm "ecs:alarm:recovery-gpu_reservation:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | ClusterName                               | Threshold |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:ECSEC2Template>ClusterName}} | 0.01      |
    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes ALARM within 180 seconds, check every 15 seconds


