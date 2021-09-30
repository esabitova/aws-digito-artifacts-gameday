@elasticache
Feature: SSM automation document Digito-ElasticacheRedisChangeReservedMemorySOP_2020-10-26

  Scenario: Execute SSM automation document Digito-ElasticacheRedisChangeReservedMemorySOP_2020-10-26 without CustomCacheParameterGroup
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                               | ResourceType |
      | resource_manager/cloud_formation_templates/ElasticacheReplicationGroupClusterEnabled.yml                      | ON_DEMAND    |
      | documents/elasticache/sop/redis_change_reserved_memory/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml  | ASSUME_ROLE  |
    And published "Digito-ElasticacheRedisChangeReservedMemorySOP_2020-10-26" SSM document
    And cache CacheParameterGroupName as "OldCacheParameterGroupName"
      | ReplicationGroupId                                                          |
      | {{cfn-output:ElasticacheReplicationGroupClusterEnabled>ReplicationGroupId}} |
    And parse "redis6-x-{{cfn-output:ElasticacheReplicationGroupClusterEnabled>ReplicationGroupId}}" and cache as CustomCacheParameterGroupName

    When SSM automation document "Digito-ElasticacheRedisChangeReservedMemorySOP_2020-10-26" executed
      | ReplicationGroupId                                                          | ReservedMemoryPercent | AutomationAssumeRole                                                                             | SNSTopicARNForManualApproval                                          | IAMPrincipalForManualApproval                                                                    | ApproveChangeMemoryReservationAutomatically |
      | {{cfn-output:ElasticacheReplicationGroupClusterEnabled>ReplicationGroupId}} | 50                    | {{cfn-output:AutomationAssumeRoleTemplate>DigitoElasticacheRedisChangeReservedMemoryAssumeRole}} | {{cfn-output:ElasticacheReplicationGroupClusterEnabled>SNSTopicName}} | {{cfn-output:ElasticacheReplicationGroupClusterEnabled>RoleApproveChangeCacheParameterGroupArn}} | true                                        |


    Then SSM automation document "Digito-ElasticacheRedisChangeReservedMemorySOP_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
