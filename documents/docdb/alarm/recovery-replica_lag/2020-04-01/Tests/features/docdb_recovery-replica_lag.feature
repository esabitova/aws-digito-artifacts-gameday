@docdb @integration @alarm

Feature: Alarm Setup - DocumentDB HighReplicaLag

  Scenario: To detect high values of DBInstanceReplicaLag - green
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                      |ResourceType | VPC                      | VPCCIDR                    | PrivateSubnet01                                | PrivateSubnet02                                | KmsKey                              |
      | resource_manager/cloud_formation_templates/shared/KMS.yml            | SHARED      |                          |                            |                                                |                                                |                                     |
      | resource_manager/cloud_formation_templates/shared/VPC.yml            | SHARED      |                          |                            |                                                |                                                |                                     |
      | resource_manager/cloud_formation_templates/DocDbTemplate.yml         | ON_DEMAND   | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>VPCCidr}} | {{cfn-output:VPC>PrivateSubnetWithInternet01}} | {{cfn-output:VPC>PrivateSubnetWithInternet02}} | {{cfn-output:KMS>EncryptAtRestKey}} |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml   | SHARED      |                          |                            |                                                |                                                |                                     |

    When alarm "docdb:alarm:recovery-replica_lag:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | DBInstanceIdentifier                                     | Threshold |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:DocDbTemplate>DBInstanceReplicaIdentifier}} | 10000     |
    Then assert metrics for all alarms are populated
    And sleep for "30" seconds
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 300 seconds, check every 15 seconds

  Scenario: To detect high values of DBInstanceReplicaLag - red
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                      |ResourceType | VPC                      | VPCCIDR                    | PrivateSubnet01                                | PrivateSubnet02                                | KmsKey                              |
      | resource_manager/cloud_formation_templates/shared/KMS.yml            | SHARED      |                          |                            |                                                |                                                |                                     |
      | resource_manager/cloud_formation_templates/shared/VPC.yml            | SHARED      |                          |                            |                                                |                                                |                                     |
      | resource_manager/cloud_formation_templates/DocDbTemplate.yml         | ON_DEMAND   | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>VPCCidr}} | {{cfn-output:VPC>PrivateSubnetWithInternet01}} | {{cfn-output:VPC>PrivateSubnetWithInternet02}} | {{cfn-output:KMS>EncryptAtRestKey}} |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml   | SHARED      |                          |                            |                                                |                                                |                                     |

    When alarm "docdb:alarm:recovery-replica_lag:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | DBInstanceIdentifier                                     | Threshold |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:DocDbTemplate>DBInstanceReplicaIdentifier}} | 1         |
    Then assert metrics for all alarms are populated
    And sleep for "30" seconds
    And wait until alarm {{alarm:under_test>AlarmName}} becomes ALARM within 300 seconds, check every 15 seconds
