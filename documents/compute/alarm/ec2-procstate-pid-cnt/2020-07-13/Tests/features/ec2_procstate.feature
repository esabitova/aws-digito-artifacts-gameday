@ec2 @integration @alarm @procstate
Feature: Alarm Setup - EC2 Dead process
  Scenario: Lease EC2 from resource manager and test attach an alarm from Document
    Given the cloud formation templates as integration test resources
      |CfnTemplatePath                                                          |ResourceType|InstanceType | AlarmGreaterThanOrEqualToThreshold |
      |resource_manager/cloud_formation_templates/EC2WithCWAgentCfnTemplate.yml |ON_DEMAND   |t2.small     | 99                                 |
      |resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml       |SHARED      |             |                                    |
    When alarm "compute:alarm:ec2-procstate-pid-cnt:2020-07-13" is installed
      |alarmId    |InstanceId                                          |Threshold | PidPath           | SNSTopicARN
      |under_test |{{cfn-output:EC2WithCWAgentCfnTemplate>InstanceId}} |   1      | /var/run/sshd.pid | {{cfn-output:SnsForAlarms>Topic}}
    Then wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 180 seconds, check every 15 seconds
