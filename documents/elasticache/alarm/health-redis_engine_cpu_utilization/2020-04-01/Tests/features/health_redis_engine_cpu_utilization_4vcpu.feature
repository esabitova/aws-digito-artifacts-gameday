@elasticache @integration @alarm
Feature: Alarm Setup - Elasticache Errors

  Scenario: Create elasticache:alarm:health-redis_engine_cpu_utilization:2020-04-01 with 4 vCPU based on EngineCPUUtilization metric and check OK status
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                   | ResourceType | NodeType        |
      | resource_manager/cloud_formation_templates/ElasticacheReplicationGroupClusterDisabledSingleAZ.yml | ON_DEMAND    | cache.m4.xlarge |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml                                | SHARED       |                 |
    And cache PrimaryClusterId and ReplicaClusterId "before" SSM automation execution
      | ReplicationGroupId                                                                   |
      | {{cfn-output:ElasticacheReplicationGroupClusterDisabledSingleAZ>ReplicationGroupId}} |
    When alarm "elasticache:alarm:health-redis_engine_cpu_utilization:2020-04-01" is installed
      | alarmId    | ClusterId                         | Threshold | SNSTopicARN                       |
      | under_test | {{cache:before>PrimaryClusterId}} | 80        | {{cfn-output:SnsForAlarms>Topic}} |
    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 300 seconds, check every 20 seconds
