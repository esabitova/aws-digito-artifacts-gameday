# @elasticache
Feature: SSM automation document Digito-RebootElasticacheClusterTest_2020-10-26

  Scenario: Execute SSM automation document Digito-RebootElasticacheClusterTest_2020-10-26
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath     | ResourceType |
      | resource_manager/cloud_formation_templates/ElasticacheClusterRedis.yml  | ON_DEMAND    |
      | documents/elasticache/test/reboot_cluster/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RebootElasticacheClusterTest_2020-10-26" SSM document
    # Add any pre-execution caching and setup steps here

    When SSM automation document "Digito-RebootElasticacheClusterTest_2020-10-26" executed
    # Add other parameter names below
      | ReplicationGroupId             | AutomationAssumeRole                                    | SyntheticAlarmName                               |
    # Replace parameter values to point to the corresponding outputs in cloudformation template
      | {{cfn-output:ElasticacheClusterRedis>ClusterId}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoElasticacheRebootClusterAssumeRole}} | {{cfn-output:ElasticacheClusterRedis>SyntheticAlarm}} |
    # Add other steps that should run parallel to the document here

    Then SSM automation document "Digito-RebootElasticacheClusterTest_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    # Add any post-execution caching and validation here