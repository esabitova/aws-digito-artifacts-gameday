@efs @integration @alarm
Feature: Alarm Setup - EFS Mount Failures (Using Metric)
  Scenario: Lease EFS from resource manager and test attach an alarm from Document
    Given the cloud formation templates as integration test resources
      |CfnTemplatePath                                                    | ResourceType
      |resource_manager/cloud_formation_templates/EFSTemplate.yml         | ON_DEMAND
      |resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml | SHARED
    When alarm "efs:alarm:mount_failure:2020-04-01" is installed
      | SNSTopicARN                       | Threshold
      | {{cfn-output:SnsForAlarms>Topic}} | 0
    And ec2 {{cfn-output:EFSTemplate>InstanceId}} is rebooted
    Then assert metrics for all alarms are populated

