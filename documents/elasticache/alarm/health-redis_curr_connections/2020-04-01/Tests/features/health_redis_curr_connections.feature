@elasticache @integration @alarm
Feature: Alarm Setup - Elasticache Errors
  Scenario: Create elasticache:alarm:health-redis_curr_connections:2020-04-01 for Redis based on CurrConnections metric and check OK status
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                   | ResourceType |
      | resource_manager/cloud_formation_templates/ElasticacheReplicationGroupClusterDisabledSingleAZ.yml | ON_DEMAND    |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml                                | SHARED       |
    And cache PrimaryClusterId and ReplicaClusterId "before" SSM automation execution
      | ReplicationGroupId                                                                   |
      | {{cfn-output:ElasticacheReplicationGroupClusterDisabledSingleAZ>ReplicationGroupId}} |
    When alarm "elasticache:alarm:health-redis_curr_connections:2020-04-01" is installed
      | alarmId    | ClusterId                         | Threshold | SNSTopicARN                       |
      | under_test | {{cache:before>PrimaryClusterId}} | 10        | {{cfn-output:SnsForAlarms>Topic}} |
    Then assert metrics for all alarms are populated
