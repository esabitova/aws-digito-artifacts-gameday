@elasticache @integration @alarm
Feature: Alarm Setup - Elasticache Errors

  Scenario: Create elasticache:alarm:memcached_host_level_cpu_utilization:2020-04-01 based on CPUUtilization metric and check OK status
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                            | ResourceType |
      | resource_manager/cloud_formation_templates/ElasticacheClusterMemcached.yml | ON_DEMAND    |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml         | SHARED       |
    When alarm "elasticache:alarm:health-memcached_host_level_cpu_utilization:2020-04-01" is installed
      | alarmId    | ClusterId                                            | Threshold | SNSTopicARN                       |
      | under_test | {{cfn-output:ElasticacheClusterMemcached>ClusterId}} | 90        | {{cfn-output:SnsForAlarms>Topic}} |
    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 300 seconds, check every 20 seconds
