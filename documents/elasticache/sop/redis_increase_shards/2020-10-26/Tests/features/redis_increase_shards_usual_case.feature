@elasticache
Feature: SSM automation document Digito-RedisIncreaseShards_2020-10-26

  Scenario: Execute SSM automation document Digito-RedisIncreaseShards_2020-10-26 without ReshardingConfiguration
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                       | ResourceType |
      | resource_manager/cloud_formation_templates/ElasticacheReplicationGroupClusterEnabled.yml              | ON_DEMAND    |
      | documents/elasticache/sop/redis_increase_shards/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RedisIncreaseShards_2020-10-26" SSM document
    And cache by "describe_replication_groups" method of "elasticache" to "before"
      | Input-ReplicationGroupId                                                    | Output-NodeGroups                    |
      | {{cfn-output:ElasticacheReplicationGroupClusterEnabled>ReplicationGroupId}} | $.ReplicationGroups[0].NodeGroups[*] |
    And cache the size of "{{cache:before>NodeGroups}}" list as "NodeGroupIdsSize" "before"
    And calculate "{{cache:before>NodeGroupIdsSize}}" "+" "1" and cache result as "NewShardCount" "before" SSM automation execution
    And cache values to "before"
      | ReplicationGroupId                                                          |
      | {{cfn-output:ElasticacheReplicationGroupClusterEnabled>ReplicationGroupId}} |
    When SSM automation document "Digito-RedisIncreaseShards_2020-10-26" executed
      | ReplicationGroupId                                                          | AutomationAssumeRole                                                                       | NewShardCount                  |
      | {{cfn-output:ElasticacheReplicationGroupClusterEnabled>ReplicationGroupId}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoElasticacheRedisIncreaseShardsAssumeRole}} | {{cache:before>NewShardCount}} |

    Then SSM automation document "Digito-RedisIncreaseShards_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And assert "RecordStartTime, VerifyReplicationGroupAvailableStatusBeforeModification, ModifyReplicationGroupShardConfiguration, VerifyReplicationGroupAvailableStatusAfterModification, OutputRecoveryTime" steps are successfully executed in order
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache by "describe_replication_groups" method of "elasticache" to "after"
      | Input-ReplicationGroupId                                                    | Output-NodeGroups                    |
      | {{cfn-output:ElasticacheReplicationGroupClusterEnabled>ReplicationGroupId}} | $.ReplicationGroups[0].NodeGroups[*] |
    And cache the size of "{{cache:after>NodeGroups}}" list as "NodeGroupIdsSize" "after"
    And assert "NodeGroupIdsSize" at "before" became not equal to "NodeGroupIdsSize" at "after"

  Scenario: Execute SSM automation document Digito-RedisIncreaseShards_2020-10-26 with ReshardingConfiguration
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                       | ResourceType |
      | resource_manager/cloud_formation_templates/ElasticacheReplicationGroupClusterEnabled.yml              | ON_DEMAND    |
      | documents/elasticache/sop/redis_increase_shards/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RedisIncreaseShards_2020-10-26" SSM document
    And cache by "describe_replication_groups" method of "elasticache" to "before"
      | Input-ReplicationGroupId                                                    | Output-NodeGroups                    |
      | {{cfn-output:ElasticacheReplicationGroupClusterEnabled>ReplicationGroupId}} | $.ReplicationGroups[0].NodeGroups[*] |
    And extract ReshardingConfiguration from "{{cache:before>NodeGroups}}" NodeGroups as "ReshardingConfiguration" to "before"
    And cache the size of "{{cache:before>NodeGroups}}" list as "NodeGroupIdsSize" "before"
    And calculate "{{cache:before>NodeGroupIdsSize}}" "+" "1" and cache result as "NewShardCount" "before" SSM automation execution
    And cache values to "before"
      | ReplicationGroupId                                                          |
      | {{cfn-output:ElasticacheReplicationGroupClusterEnabled>ReplicationGroupId}} |
    And generate new ReshardingConfiguration as "ReshardingConfiguration" "input"
      | CurrentReshardingConfiguration           | NewShardCount                  |
      | {{cache:before>ReshardingConfiguration}} | {{cache:before>NewShardCount}} |
    And destring "{{cache:input>ReshardingConfiguration}}" ReshardingConfiguration as "ReshardingConfigurationDestringed" to "input"
    When SSM automation document "Digito-RedisIncreaseShards_2020-10-26" executed
      | ReplicationGroupId                                                          | AutomationAssumeRole                                                                       | NewShardCount                  | NewReshardingConfiguration              |
      | {{cfn-output:ElasticacheReplicationGroupClusterEnabled>ReplicationGroupId}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoElasticacheRedisIncreaseShardsAssumeRole}} | {{cache:before>NewShardCount}} | {{cache:input>ReshardingConfiguration}} |

    Then SSM automation document "Digito-RedisIncreaseShards_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And assert "RecordStartTime, VerifyReplicationGroupAvailableStatusBeforeModification, ModifyReplicationGroupShardConfiguration, VerifyReplicationGroupAvailableStatusAfterModification, OutputRecoveryTime" steps are successfully executed in order
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache by "describe_replication_groups" method of "elasticache" to "after"
      | Input-ReplicationGroupId                                                    | Output-NodeGroups                    |
      | {{cfn-output:ElasticacheReplicationGroupClusterEnabled>ReplicationGroupId}} | $.ReplicationGroups[0].NodeGroups[*] |
    And extract ReshardingConfiguration from "{{cache:after>NodeGroups}}" NodeGroups as "ReshardingConfiguration" to "after"
    And cache the size of "{{cache:after>NodeGroups}}" list as "NodeGroupIdsSize" "after"
    And assert the difference between "NodeGroupIdsSize" at "after" and "NodeGroupIdsSize" at "before" became "1"
    And assert "ReshardingConfigurationDestringed" at "input" became equal to "ReshardingConfiguration" at "after" without order of PreferredAvailabilityZones
