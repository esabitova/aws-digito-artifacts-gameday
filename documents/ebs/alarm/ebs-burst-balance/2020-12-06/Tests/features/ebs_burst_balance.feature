@ebs @integration @alarm @drained_burst
Feature: Alarm Setup - EBS Drained burst balance
  Scenario: Lease EBS from resource manager and test attach an alarm from Document
    Given the cloud formation templates as integration test resources
      |CfnTemplatePath                                                      |ResourceType|InstanceType |
      |resource_manager/cloud_formation_templates/Ec2WithEbsCfnTemplate.yml |ON_DEMAND   |t2.small     |
      |resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml   |SHARED      |             |
    When alarm "ebs:alarm:ebs-burst-balance:2020-12-06" is installed
      |alarmId    |VolumeId                                          |Threshold | SNSTopicARN
      |under_test |{{cfn-output:Ec2WithEbsCfnTemplate>VolumeId}} |   30      | {{cfn-output:SnsForAlarms>Topic}}
    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 180 seconds, check every 15 seconds
