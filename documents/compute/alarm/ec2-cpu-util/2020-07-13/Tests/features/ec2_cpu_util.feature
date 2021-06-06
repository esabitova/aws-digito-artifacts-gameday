@ec2 @integration @alarm @cpu
Feature: Alarm Setup - EC2 CPU utilization
  Scenario: Lease EC2 from resource manager and test attach an alarm from Document
    Given the cloud formation templates as integration test resources
      |CfnTemplatePath                                                          |ResourceType|InstanceType | AlarmGreaterThanOrEqualToThreshold |
      |resource_manager/cloud_formation_templates/EC2WithCWAgentCfnTemplate.yml |ON_DEMAND   |t2.small     | 99                                 |
      |resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml       |SHARED      |             |                                    |
    When alarm "compute:alarm:ec2-cpu-util:2020-07-13" is installed
      |alarmId    |InstanceId                                          |Threshold  | SNSTopicARN
      |under_test |{{cfn-output:EC2WithCWAgentCfnTemplate>InstanceId}} |   1      | {{cfn-output:SnsForAlarms>Topic}}
    Then assert metrics for all alarms are populated

