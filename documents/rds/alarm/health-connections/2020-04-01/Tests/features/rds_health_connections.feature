@rds @integration @alarm @connections
Feature: Alarm Setup - RDS Connection spike
  Scenario: Lease RDS from resource manager and test attach an alarm from Document
    Given the cloud formation templates as integration test resources
      |CfnTemplatePath                                                       |ResourceType|DBInstanceClass|AllocatedStorage|
      | resource_manager/cloud_formation_templates/RdsCfnTemplate.yml      | ON_DEMAND    | db.t3.small     | 20               |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml | SHARED       |                 |                  |
    When alarm "rds:alarm:health-connections:2020-04-01" is installed
      |alarmId    |DBInstanceIdentifier                     |Threshold | SNSTopicARN
      |under_test |{{cfn-output:RdsCfnTemplate>InstanceId}} |   1      | {{cfn-output:SnsForAlarms>Topic}}
    Then assert metrics for all alarms are populated
