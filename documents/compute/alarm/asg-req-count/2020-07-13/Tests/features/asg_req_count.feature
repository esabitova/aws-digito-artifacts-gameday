@asg @integration @alarm @req
Feature: Alarm Setup - ASG Abnormal requests per target
  Scenario: Lease ASG from resource manager and test attach an alarm from Document
    Given the cloud formation templates as integration test resources
      |CfnTemplatePath                                                       |ResourceType|InstanceType |
      |resource_manager/cloud_formation_templates/AsgCfnTemplate.yml         |ON_DEMAND   |t2.small     |
      |resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml    |SHARED      |             |
    When alarm "compute:alarm:asg-req-count:2020-07-13" is installed
      |alarmId    |TargetGroup                                           |Threshold |SNSTopicARN
      |under_test |{{cfn-output:AsgCfnTemplate>LoadBalancerTargetGroup}} |1         |{{cfn-output:SnsForAlarms>Topic}}
    Then assert metrics for all alarms are populated

