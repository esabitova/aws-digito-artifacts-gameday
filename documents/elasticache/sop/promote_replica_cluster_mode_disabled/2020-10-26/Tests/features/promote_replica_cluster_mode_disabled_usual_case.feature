@elasticache
Feature: SSM automation document Digito-PromoteReplicaClusterModeDisabled_2020-10-26

  Scenario: Execute SSM automation document Digito-PromoteReplicaClusterModeDisabled_2020-10-26
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                                       | ResourceType |
      | resource_manager/cloud_formation_templates/ElasticacheReplicationGroupClusterDisabledMultiAZ.yml                      | ON_DEMAND    |
      | documents/elasticache/sop/promote_replica_cluster_mode_disabled/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-PromoteReplicaClusterModeDisabled_2020-10-26" SSM document
    And cache PrimaryClusterId and ReplicaClusterId "before" SSM automation execution
      | ReplicationGroupId                                                                  |
      | {{cfn-output:ElasticacheReplicationGroupClusterDisabledMultiAZ>ReplicationGroupId}} |

    When SSM automation document "Digito-PromoteReplicaClusterModeDisabled_2020-10-26" executed
      | ReplicationGroupId                                                                  | NewPrimaryClusterId               | AutomationAssumeRole                                                                                     |
      | {{cfn-output:ElasticacheReplicationGroupClusterDisabledMultiAZ>ReplicationGroupId}} | {{cache:before>ReplicaClusterId}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoElasticachePromoteReplicaClusterModeDisabledAssumeRole}} |

    Then SSM automation document "Digito-PromoteReplicaClusterModeDisabled_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache PrimaryClusterId and ReplicaClusterId "after" SSM automation execution
      | ReplicationGroupId                                                                  |
      | {{cfn-output:ElasticacheReplicationGroupClusterDisabledMultiAZ>ReplicationGroupId}} |

    Then assert "ReplicaClusterId" at "before" became equal to "PrimaryClusterId" at "after"
    Then assert "PrimaryClusterId" at "before" became equal to "ReplicaClusterId" at "after"