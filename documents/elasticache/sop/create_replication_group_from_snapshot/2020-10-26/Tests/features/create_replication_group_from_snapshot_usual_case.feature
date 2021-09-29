@elasticache
Feature: SSM automation document Digito-CreateElasticacheReplicationGroupFromSnapshotSOP_2020-10-26

  Scenario: Execute SSM automation document Digito-CreateElasticacheReplicationGroupFromSnapshotSOP_2020-10-26 when source cluster available and cluster mode disabled
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                                        | ResourceType |
      | resource_manager/cloud_formation_templates/ElasticacheReplicationGroupClusterDisabledSingleAZ.yml                      | ON_DEMAND    |
      | documents/elasticache/sop/create_replication_group_from_snapshot/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-CreateElasticacheReplicationGroupFromSnapshotSOP_2020-10-26" SSM document
    And cache replication group settings as "SourceReplicationGroupSettings" "before" SSM automation execution
      | ReplicationGroupId                                                                   |
      | {{cfn-output:ElasticacheReplicationGroupClusterDisabledSingleAZ>ReplicationGroupId}} |
    And create snapshot and cache as "SnapshotName" "before" SSM automation execution
      | ReplicationGroupId                                                                   |
      | {{cfn-output:ElasticacheReplicationGroupClusterDisabledSingleAZ>ReplicationGroupId}} |
    And generate replication group ID and cache as "TargetReplicationGroupId" "before" SSM automation execution

    When SSM automation document "Digito-CreateElasticacheReplicationGroupFromSnapshotSOP_2020-10-26" executed
      | SourceSnapshotName            | TargetReplicationGroupId                  | AutomationAssumeRole                                                                                  |
      | {{cache:before>SnapshotName}} | {{cache:before>TargetReplicationGroupId}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoElasticacheCreateCacheClusterFromSnapshotAssumeRole}} |

    Then SSM automation document "Digito-CreateElasticacheReplicationGroupFromSnapshotSOP_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache replication group settings as "TargetReplicationGroupSettings" "after" SSM automation execution
      | ReplicationGroupId                        |
      | {{cache:before>TargetReplicationGroupId}} |

    Then assert "SourceReplicationGroupSettings" at "before" became equal to "TargetReplicationGroupSettings" at "after"
    And assert "RecordStartTime,AssertSnapshotAvailableStatus,DescribeSnapshot,CreateReplicationGroupFromSnapshot,VerifyReplicationGroupStatus,OutputRecoveryTime" steps are successfully executed in order
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |


  Scenario: Execute SSM automation document Digito-CreateElasticacheReplicationGroupFromSnapshotSOP_2020-10-26 when source cluster available and cluster mode enabled
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                                        | ResourceType |
      | resource_manager/cloud_formation_templates/ElasticacheReplicationGroupClusterEnabled.yml                               | ON_DEMAND    |
      | documents/elasticache/sop/create_replication_group_from_snapshot/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-CreateElasticacheReplicationGroupFromSnapshotSOP_2020-10-26" SSM document
    And cache replication group settings as "SourceReplicationGroupSettings" "before" SSM automation execution
      | ReplicationGroupId                                                          |
      | {{cfn-output:ElasticacheReplicationGroupClusterEnabled>ReplicationGroupId}} |
    And create snapshot and cache as "SnapshotName" "before" SSM automation execution
      | ReplicationGroupId                                                          |
      | {{cfn-output:ElasticacheReplicationGroupClusterEnabled>ReplicationGroupId}} |
    And generate replication group ID and cache as "TargetReplicationGroupId" "before" SSM automation execution

    When SSM automation document "Digito-CreateElasticacheReplicationGroupFromSnapshotSOP_2020-10-26" executed
      | SourceSnapshotName            | TargetReplicationGroupId                  | AutomationAssumeRole                                                                                  |
      | {{cache:before>SnapshotName}} | {{cache:before>TargetReplicationGroupId}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoElasticacheCreateCacheClusterFromSnapshotAssumeRole}} |

    Then SSM automation document "Digito-CreateElasticacheReplicationGroupFromSnapshotSOP_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache replication group settings as "TargetReplicationGroupSettings" "after" SSM automation execution
      | ReplicationGroupId                        |
      | {{cache:before>TargetReplicationGroupId}} |

    Then assert "SourceReplicationGroupSettings" at "before" became equal to "TargetReplicationGroupSettings" at "after"
    And assert "RecordStartTime,AssertSnapshotAvailableStatus,DescribeSnapshot,CreateReplicationGroupFromSnapshot,VerifyReplicationGroupStatus,OutputRecoveryTime" steps are successfully executed in order
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
