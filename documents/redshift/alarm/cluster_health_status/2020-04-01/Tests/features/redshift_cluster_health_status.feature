@redshift @integration @alarm
Feature: Alarm Setup - redshift Cluster_HealthStatus
  Scenario: Create redshift:alarm:cluster_health_status:2020-04-01 based on HealthStatus metric and check OK status
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                    | ResourceType | KmsKey                              | VPC                      | PublicSubnetOne                    | PublicSubnetTwo                    | PublicSubnet1Cidr                    | PublicSubnet2Cidr                    |
      | resource_manager/cloud_formation_templates/shared/KMS.yml          | SHARED       |                                     |                          |                                    |                                    |                                      |                                      |
      | resource_manager/cloud_formation_templates/shared/VPC.yml          | SHARED       |                                     |                          |                                    |                                    |                                      |                                      |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml | SHARED       |                                     |                          |                                    |                                    |                                      |                                      |
      | resource_manager/cloud_formation_templates/RedshiftTemplate.yml    | ON_DEMAND    | {{cfn-output:KMS>EncryptAtRestKey}} | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>PublicSubnetOne}} | {{cfn-output:VPC>PublicSubnetTwo}} | {{cfn-output:VPC>PublicSubnet1Cidr}} | {{cfn-output:VPC>PublicSubnet2Cidr}} |
    When alarm "redshift:alarm:cluster_health_status:2020-04-01" is installed
      | alarmId    | ClusterName                                 | Threshold | EvaluationPeriods | DatapointsToAlarm | SNSTopicARN                       |
      | under_test | {{cfn-output:RedshiftTemplate>ClusterName}} | 1         | 1                 | 1                 | {{cfn-output:SnsForAlarms>Topic}} |
    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 180 seconds, check every 15 seconds
