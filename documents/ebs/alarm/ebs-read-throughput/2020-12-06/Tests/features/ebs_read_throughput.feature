@ebs @integration @alarm @read_throughput
Feature: Alarm Setup - EBS Read throughput
  Scenario: Lease EBS from resource manager and test attach an alarm from Document
    Given the cloud formation templates as integration test resources
      |CfnTemplatePath                                                      |ResourceType|InstanceType | KmsKey                              |
      |resource_manager/cloud_formation_templates/shared/KMS.yml            |SHARED      |             |                                     |
      |resource_manager/cloud_formation_templates/Ec2WithEbsCfnTemplate.yml |ON_DEMAND   |t2.small     | {{cfn-output:KMS>EncryptAtRestKey}} |
      |resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml   |SHARED      |             |                                     |
    When alarm "ebs:alarm:ebs-read-throughput:2020-12-06" is installed
      |alarmId    |VolumeId                                      |BandWidth | SNSTopicARN
      |under_test |{{cfn-output:Ec2WithEbsCfnTemplate>VolumeId}} |   1      | {{cfn-output:SnsForAlarms>Topic}}
    Then assert metrics for all alarms are populated
