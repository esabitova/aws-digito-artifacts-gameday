@ec2 @integration @alarm @memory
Feature: Alarm Setup - EC2 Memory Utilization (via CloudWatch Agent)
  Scenario: Lease EC2 from resource manager and test attach an alarm from Document
    Given the cloud formation templates as integration test resources
      |CfnTemplatePath                                                          |ResourceType|InstanceType | AlarmGreaterThanOrEqualToThreshold |
      |resource_manager/cloud_formation_templates/EC2WithCWAgentCfnTemplate.yml |ON_DEMAND   |t2.small     | 99                                 |
      |resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml       |SHARED      |             |                                    |
    When alarm "compute:alarm:ec2-cloudwatch-mem-util:2021-04-05" is installed
      |alarmId    |InstanceId                                          | Threshold | SNSTopicARN
      |under_test |{{cfn-output:EC2WithCWAgentCfnTemplate>InstanceId}} | 1         | {{cfn-output:SnsForAlarms>Topic}}
    Then assert metrics for all alarms are populated

