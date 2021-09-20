@elasticache @integration @alarm
Feature: Alarm Setup - Elasticache Errors
  Scenario: Create elasticache:alarm:health-memcached_evictions:2020-04-01 for Memcached based on Evictions metric and check OK status
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                            | ResourceType |
      | resource_manager/cloud_formation_templates/ElasticacheClusterMemcached.yml | ON_DEMAND    |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml         | SHARED       |
    When alarm "elasticache:alarm:health-memcached_evictions:2020-04-01" is installed
      | alarmId    | ClusterId                                            | Threshold | SNSTopicARN                       |
      | under_test | {{cfn-output:ElasticacheClusterMemcached>ClusterId}} | 10        | {{cfn-output:SnsForAlarms>Topic}} |
    Then assert metrics for all alarms are populated
