@docdb @integration @alarm
Feature: Alarm Setup - DocDb Errors
  Scenario: Test DocDb  time taken per disk I/O operation:alarm:health-write_latency:2020-04-01
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                      |ResourceType | VPC                      | VPCCIDR                    | PrivateSubnet01                                | PrivateSubnet02                                |
      | resource_manager/cloud_formation_templates/shared/VPC.yml            | SHARED      |                          |                            |                                                |                                                |
      | resource_manager/cloud_formation_templates/DocDbTemplate.yml         | ON_DEMAND   | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>VPCCidr}} | {{cfn-output:VPC>PrivateSubnetWithInternet01}} | {{cfn-output:VPC>PrivateSubnetWithInternet02}} |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml   | SHARED      |                          |                            |                                                |                                                |
    When alarm "docdb:alarm:health-write_latency:2020-04-01" is installed
      |alarmId    |DBInstancePrimaryIdentifier                              | Threshold   | SNSTopicARN                       |
      |under_test |{{cfn-output:DocDbTemplate>DBInstancePrimaryIdentifier}} | 1           | {{cfn-output:SnsForAlarms>Topic}} |
    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 120 seconds, check every 20 seconds

