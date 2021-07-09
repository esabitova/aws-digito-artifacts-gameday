@docdb @integration @alarm
Feature: Alarm Setup - DocumentDb HighVolumeReadIOPS

  Scenario: To detect anomalies of high values of VolumeReadIOPs
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                    | ResourceType |
      | resource_manager/cloud_formation_templates/DocDbTemplate.yml       | ON_DEMAND    |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml | SHARED       |
    When alarm "docdb:alarm:usage-high_volume_read_iops:2020-04-01" is installed
      | SNSTopicARN                       | DBClusterIdentifier                              | Threshold |
      | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} | 5         |
    Then assert metrics for all alarms are populated
