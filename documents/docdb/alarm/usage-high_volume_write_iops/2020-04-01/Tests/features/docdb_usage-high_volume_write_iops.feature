@docdb @integration @alarm
Feature: Alarm Setup - DocumentDb HighVolumeWriteIOPS

  Scenario: To detect anomalies of high values of VolumeWriteIOPs
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                      |ResourceType | VPC                      | VPCCIDR                    | PrivateSubnet01                                | PrivateSubnet02                                |
      | resource_manager/cloud_formation_templates/shared/VPC.yml            | SHARED      |                          |                            |                                                |                                                |
      | resource_manager/cloud_formation_templates/DocDbTemplate.yml         | ON_DEMAND   | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>VPCCidr}} | {{cfn-output:VPC>PrivateSubnetWithInternet01}} | {{cfn-output:VPC>PrivateSubnetWithInternet02}} |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml   | SHARED      |                          |                            |                                                |                                                |

    When alarm "docdb:alarm:usage-high_volume_write_iops:2020-04-01" is installed
      | SNSTopicARN                       | DBClusterIdentifier                              | Threshold |
      | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} | 5         |
    Then assert metrics for all alarms are populated
