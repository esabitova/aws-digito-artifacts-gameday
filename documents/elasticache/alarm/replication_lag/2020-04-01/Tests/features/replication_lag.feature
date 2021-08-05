@elasticache @integration @alarm
Feature: Alarm Setup - Elasticache Errors

  Scenario: Test Elasticache Redis ReplicationLag Alarm elasticache:alarm:replication_lag:2020-04-01
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                          | ResourceType |
      | resource_manager/cloud_formation_templates/ElasticacheReplicationGroupClusterEnabled.yml | ON_DEMAND    |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml                       | SHARED       |
    And cache PrimaryClusterId and ReplicaClusterId "before" SSM automation execution
      | ReplicationGroupId                                                          |
      | {{cfn-output:ElasticacheReplicationGroupClusterEnabled>ReplicationGroupId}} |
    When alarm "elasticache:alarm:replication_lag:2020-04-01" is installed
      | alarmId    | CacheClusterId                    | Threshold | SNSTopicARN                       |
      | under_test | {{cache:before>ReplicaClusterId}} | 1000      | {{cfn-output:SnsForAlarms>Topic}} |
    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 300 seconds, check every 20 seconds
