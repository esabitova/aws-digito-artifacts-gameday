@elasticache
Feature: SSM automation document Digito-PromoteElasticacheReplicaClusterModeDisabledSOP_2020-10-26

  Scenario: Execute SSM automation document Digito-PromoteElasticacheReplicaClusterModeDisabledSOP_2020-10-26 with AutomaticFailover disabled in a single AZ deployment
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                                       | ResourceType | AutomaticFailoverEnabled |
      | resource_manager/cloud_formation_templates/ElasticacheReplicationGroupClusterDisabledSingleAZ.yml                     | ON_DEMAND    | False                    |
      | documents/elasticache/sop/promote_replica_cluster_mode_disabled/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                          |
    And published "Digito-PromoteElasticacheReplicaClusterModeDisabledSOP_2020-10-26" SSM document
    And cache PrimaryClusterId and ReplicaClusterId "before" SSM automation execution
      | ReplicationGroupId                                                                   |
      | {{cfn-output:ElasticacheReplicationGroupClusterDisabledSingleAZ>ReplicationGroupId}} |

    When SSM automation document "Digito-PromoteElasticacheReplicaClusterModeDisabledSOP_2020-10-26" executed
      | ReplicationGroupId                                                                   | NewPrimaryClusterId               | AutomationAssumeRole                                                                                        |
      | {{cfn-output:ElasticacheReplicationGroupClusterDisabledSingleAZ>ReplicationGroupId}} | {{cache:before>ReplicaClusterId}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoPromoteElasticacheReplicaClusterModeDisabledSOPAssumeRole}} |

    Then SSM automation document "Digito-PromoteElasticacheReplicaClusterModeDisabledSOP_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache PrimaryClusterId and ReplicaClusterId "after" SSM automation execution
      | ReplicationGroupId                                                                   |
      | {{cfn-output:ElasticacheReplicationGroupClusterDisabledSingleAZ>ReplicationGroupId}} |

    Then assert "ReplicaClusterId" at "before" became equal to "PrimaryClusterId" at "after"
    And assert "RecordStartTime,AssertClusterModeDisabled,GetFailoverSettings,VerifyAutomaticFailoverStatus,PromoteReplica,VerifyReplicationGroupStatusAfterPromoteReplica,VerifyAutomaticFailoverStatusBeforeRestore,OutputRecoveryTime" steps are successfully executed in order
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |


  Scenario: Execute SSM automation document Digito-PromoteElasticacheReplicaClusterModeDisabledSOP_2020-10-26 with AutomaticFailover enabled in a single AZ deployment
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                                       | ResourceType | AutomaticFailoverEnabled |
      | resource_manager/cloud_formation_templates/ElasticacheReplicationGroupClusterDisabledSingleAZ.yml                     | ON_DEMAND    | True                     |
      | documents/elasticache/sop/promote_replica_cluster_mode_disabled/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                          |
    And published "Digito-PromoteElasticacheReplicaClusterModeDisabledSOP_2020-10-26" SSM document
    And cache PrimaryClusterId and ReplicaClusterId "before" SSM automation execution
      | ReplicationGroupId                                                                   |
      | {{cfn-output:ElasticacheReplicationGroupClusterDisabledSingleAZ>ReplicationGroupId}} |
    And cache FailoverSettings "before" SSM automation execution
      | ReplicationGroupId                                                                   |
      | {{cfn-output:ElasticacheReplicationGroupClusterDisabledSingleAZ>ReplicationGroupId}} |
    And register FailoverSettings for teardown

    When SSM automation document "Digito-PromoteElasticacheReplicaClusterModeDisabledSOP_2020-10-26" executed
      | ReplicationGroupId                                                                   | NewPrimaryClusterId               | AutomationAssumeRole                                                                                        |
      | {{cfn-output:ElasticacheReplicationGroupClusterDisabledSingleAZ>ReplicationGroupId}} | {{cache:before>ReplicaClusterId}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoPromoteElasticacheReplicaClusterModeDisabledSOPAssumeRole}} |

    Then SSM automation document "Digito-PromoteElasticacheReplicaClusterModeDisabledSOP_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache PrimaryClusterId and ReplicaClusterId "after" SSM automation execution
      | ReplicationGroupId                                                                   |
      | {{cfn-output:ElasticacheReplicationGroupClusterDisabledSingleAZ>ReplicationGroupId}} |
    And cache FailoverSettings "after" SSM automation execution
      | ReplicationGroupId                                                                   |
      | {{cfn-output:ElasticacheReplicationGroupClusterDisabledSingleAZ>ReplicationGroupId}} |

    Then assert "ReplicaClusterId" at "before" became equal to "PrimaryClusterId" at "after"
    And assert "FailoverSettings" at "before" became equal to "FailoverSettings" at "after"
    And assert "RecordStartTime,AssertClusterModeDisabled,GetFailoverSettings,VerifyAutomaticFailoverStatus,UpdateFailoverSettings,VerifyReplicationGroupStatusAfterUpdateFailoverSettings,PromoteReplica,VerifyReplicationGroupStatusAfterPromoteReplica,VerifyAutomaticFailoverStatusBeforeRestore,RestoreFailoverSettings,VerifyReplicationGroupStatusAfterRestoreFailoverSettings,OutputRecoveryTime" steps are successfully executed in order
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |


  Scenario: Execute SSM automation document Digito-PromoteElasticacheReplicaClusterModeDisabledSOP_2020-10-26 with AutomaticFailover and MultiAZ enabled in a multi AZ deployment
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                                       | ResourceType |
      | resource_manager/cloud_formation_templates/ElasticacheReplicationGroupClusterDisabledMultiAZ.yml                      | ON_DEMAND    |
      | documents/elasticache/sop/promote_replica_cluster_mode_disabled/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-PromoteElasticacheReplicaClusterModeDisabledSOP_2020-10-26" SSM document
    And cache PrimaryClusterId and ReplicaClusterId "before" SSM automation execution
      | ReplicationGroupId                                                                  |
      | {{cfn-output:ElasticacheReplicationGroupClusterDisabledMultiAZ>ReplicationGroupId}} |
    And cache FailoverSettings "before" SSM automation execution
      | ReplicationGroupId                                                                  |
      | {{cfn-output:ElasticacheReplicationGroupClusterDisabledMultiAZ>ReplicationGroupId}} |
    And register FailoverSettings for teardown

    When SSM automation document "Digito-PromoteElasticacheReplicaClusterModeDisabledSOP_2020-10-26" executed
      | ReplicationGroupId                                                                  | NewPrimaryClusterId               | AutomationAssumeRole                                                                                        |
      | {{cfn-output:ElasticacheReplicationGroupClusterDisabledMultiAZ>ReplicationGroupId}} | {{cache:before>ReplicaClusterId}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoPromoteElasticacheReplicaClusterModeDisabledSOPAssumeRole}} |

    Then SSM automation document "Digito-PromoteElasticacheReplicaClusterModeDisabledSOP_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache PrimaryClusterId and ReplicaClusterId "after" SSM automation execution
      | ReplicationGroupId                                                                  |
      | {{cfn-output:ElasticacheReplicationGroupClusterDisabledMultiAZ>ReplicationGroupId}} |
    And cache FailoverSettings "after" SSM automation execution
      | ReplicationGroupId                                                                  |
      | {{cfn-output:ElasticacheReplicationGroupClusterDisabledMultiAZ>ReplicationGroupId}} |

    Then assert "ReplicaClusterId" at "before" became equal to "PrimaryClusterId" at "after"
    And assert "FailoverSettings" at "before" became equal to "FailoverSettings" at "after"
    And assert "RecordStartTime,AssertClusterModeDisabled,GetFailoverSettings,VerifyAutomaticFailoverStatus,UpdateFailoverSettings,VerifyReplicationGroupStatusAfterUpdateFailoverSettings,PromoteReplica,VerifyReplicationGroupStatusAfterPromoteReplica,VerifyAutomaticFailoverStatusBeforeRestore,RestoreFailoverSettings,VerifyReplicationGroupStatusAfterRestoreFailoverSettings,OutputRecoveryTime" steps are successfully executed in order
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
