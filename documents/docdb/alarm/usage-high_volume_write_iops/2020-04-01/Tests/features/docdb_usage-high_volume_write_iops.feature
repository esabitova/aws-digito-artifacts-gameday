@docdb @integration @alarm
Feature: Alarm Setup - DocumentDb HighVolumeWriteIOPS

  Scenario: To detect anomalies of high values of VolumeWriteIOPs
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                    | ResourceType | KmsKey                              |
      | resource_manager/cloud_formation_templates/shared/KMS.yml          | SHARED       |                                     |
      | resource_manager/cloud_formation_templates/DocDbTemplate.yml       | ON_DEMAND    | {{cfn-output:KMS>EncryptAtRestKey}} |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml | SHARED       |                                     |
    When alarm "docdb:alarm:usage-high_volume_write_iops:2020-04-01" is installed
      | SNSTopicARN                       | DBClusterIdentifier                              | Threshold |
      | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} | 5         |
    Then assert metrics for all alarms are populated
