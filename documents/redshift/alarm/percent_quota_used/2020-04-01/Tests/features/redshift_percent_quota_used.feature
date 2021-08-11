@redshift @integration @alarm
Feature: Alarm Setup - redshift Cluster_Schema_PercentageQuotaUsed
  Scenario: Create redshift:alarm:percent_quota_used:2020-04-01 based on PercentageQuotaUsed metric and check OK status
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                    | ResourceType | KmsKey                              | VPC                      | PublicSubnetOne                    | PublicSubnetTwo                    | PublicSubnet1Cidr                    | PublicSubnet2Cidr                    |
      | resource_manager/cloud_formation_templates/shared/KMS.yml          | SHARED       |                                     |                          |                                    |                                    |                                      |                                      |
      | resource_manager/cloud_formation_templates/shared/VPC.yml          | SHARED       |                                     |                          |                                    |                                    |                                      |                                      |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml | SHARED       |                                     |                          |                                    |                                    |                                      |                                      |
      | resource_manager/cloud_formation_templates/RedshiftTemplate.yml    | ON_DEMAND    | {{cfn-output:KMS>EncryptAtRestKey}} | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>PublicSubnetOne}} | {{cfn-output:VPC>PublicSubnetTwo}} | {{cfn-output:VPC>PublicSubnet1Cidr}} | {{cfn-output:VPC>PublicSubnet2Cidr}} |
    And trigger lambda "{{cfn-output:RedshiftTemplate>LambdaArn}}" asynchronously
    When alarm "redshift:alarm:percent_quota_used:2020-04-01" is installed
      | alarmId    | ClusterName                                 | DatabaseName                                 | SchemaName                                 | Threshold | EvaluationPeriods | DatapointsToAlarm | SNSTopicARN                       |
      | under_test | {{cfn-output:RedshiftTemplate>ClusterName}} | {{cfn-output:RedshiftTemplate>DatabaseName}} | {{cfn-output:RedshiftTemplate>SchemaName}} | 80        | 1                 | 1                 | {{cfn-output:SnsForAlarms>Topic}} |
    Then assert metrics for all alarms are populated within 1200 seconds, check every 15 seconds
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 300 seconds, check every 15 seconds


