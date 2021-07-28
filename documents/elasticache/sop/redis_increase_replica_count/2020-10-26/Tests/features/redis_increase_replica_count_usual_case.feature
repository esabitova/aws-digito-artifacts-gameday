@elasticache
Feature: SSM automation document Digito-RedisIncreaseReplicaCount_2020-10-26

  Scenario: Execute SSM automation document Digito-RedisIncreaseReplicaCount_2020-10-26 to increase redis replica count with Desired Replicas specified
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                               | ResourceType |
      | resource_manager/cloud_formation_templates/ElasticacheReplicationGroupClusterDisabledSingleAZ.yml             | ON_DEMAND    |
      | documents/elasticache/sop/redis_increase_replica_count/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml  | ASSUME_ROLE  |
    And published "Digito-RedisIncreaseReplicaCount_2020-10-26" SSM document
    And register redis replication group replica count for teardown
      | ReplicationGroupId                                                                    |
      | {{cfn-output:ElasticacheReplicationGroupClusterDisabledSingleAZ>ReplicationGroupId}}  |
    And cache replica count as "OldReplicaCount" "before" SSM automation execution
      | ReplicationGroupId                                                                    |
      | {{cfn-output:ElasticacheReplicationGroupClusterDisabledSingleAZ>ReplicationGroupId}}  |
    And calculate "{{cache:before>OldReplicaCount}}" "+" "1" and cache result as "NewReplicaCount" "before" SSM automation execution

    When SSM automation document "Digito-RedisIncreaseReplicaCount_2020-10-26" executed
      | ReplicationGroupId                                                                   | NewReplicaCount                  | AutomationAssumeRole                                                                             |
      | {{cfn-output:ElasticacheReplicationGroupClusterDisabledSingleAZ>ReplicationGroupId}} | {{cache:before>NewReplicaCount}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoElasticacheRedisIncreaseReplicaCountAssumeRole}} |

    Then SSM automation document "Digito-RedisIncreaseReplicaCount_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And assert "RecordStartTime, IncreaseReplicaCount, VerifyReplicationGroupStatus, OutputRecoveryTime" steps are successfully executed in order
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache replica count as "NewReplicaCount" "after" SSM automation execution
      | ReplicationGroupId                                                                    |
      | {{cfn-output:ElasticacheReplicationGroupClusterDisabledSingleAZ>ReplicationGroupId}}  |
    And assert "NewReplicaCount" at "before" became equal to "NewReplicaCount" at "after"
    And assert "OldReplicaCount" at "before" became not equal to "NewReplicaCount" at "after"
