@docdb @integration @alarm
Feature: Alarm Setup - DocumentDb HighVolumeReadIOPS

  Scenario: To detect anomalies of high values of VolumeReadIOPs
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                      |ResourceType | VPC                      | VPCCIDR                    | PrivateSubnet01                                | PrivateSubnet02                                | KmsKey                              |
      | resource_manager/cloud_formation_templates/shared/KMS.yml            | SHARED      |                          |                            |                                                |                                                |                                     |
      | resource_manager/cloud_formation_templates/shared/VPC.yml            | SHARED      |                          |                            |                                                |                                                |                                     |
      | resource_manager/cloud_formation_templates/DocDbTemplate.yml         | ON_DEMAND   | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>VPCCidr}} | {{cfn-output:VPC>PrivateSubnetWithInternet01}} | {{cfn-output:VPC>PrivateSubnetWithInternet02}} | {{cfn-output:KMS>EncryptAtRestKey}} |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml   | SHARED      |                          |                            |                                                |                                                |                                     |

    When alarm "docdb:alarm:usage-high_volume_read_iops:2020-04-01" is installed
      | SNSTopicARN                       | DBClusterIdentifier                              | Threshold |
      | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} | 5         |
    Then assert metrics for all alarms are populated
