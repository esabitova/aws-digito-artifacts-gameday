@docdb @integration @alarm
Feature: Alarm Setup - DocumentDb HighVolumeSize

  Scenario: To detect high values of VolumeBytesUsed - green
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                    | ResourceType | KmsKey                              |
      | resource_manager/cloud_formation_templates/shared/KMS.yml          | SHARED       |                                     |
      | resource_manager/cloud_formation_templates/DocDbTemplate.yml       | ON_DEMAND    | {{cfn-output:KMS>EncryptAtRestKey}} |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml | SHARED       |                                     |
    When alarm "docdb:alarm:usage-volume_bytes_used:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | DBClusterIdentifier                              | Threshold     |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} | 1099511627776 |
    Then assert metrics for all alarms are populated
    And sleep for "60" seconds
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 300 seconds, check every 15 seconds

  Scenario: To detect high values of VolumeBytesUsed - red
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                    | ResourceType |                                     |
      | resource_manager/cloud_formation_templates/shared/KMS.yml          | SHARED       |                                     |
      | resource_manager/cloud_formation_templates/DocDbTemplate.yml       | ON_DEMAND    | {{cfn-output:KMS>EncryptAtRestKey}} |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml | SHARED       |                                     |
    When alarm "docdb:alarm:usage-volume_bytes_used:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | DBClusterIdentifier                              | Threshold |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} | 1024      |
    Then assert metrics for all alarms are populated
    And sleep for "60" seconds
    And wait until alarm {{alarm:under_test>AlarmName}} becomes ALARM within 300 seconds, check every 15 seconds
