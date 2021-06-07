# Id
elasticache:sop:promote_replica_cluster_mode_disabled:2020-10-26

## Intent
Promote a replica (e.g. in case of HW failure) if cluster mode disabled

## Type
Hardware Outage SOP

## Risk
Medium

## Requirements
* ElastiCache

## Permission required for AutomationAssumeRole
* elasticache:ModifyReplicationGroup
* elasticache:DescribeReplicationGroups

## Supports Rollback
No.

## Inputs

### ReplicationGroupId

* Description: (Required) The ElastiCache Replication Group ID.
* Type: String

### ReplicationGroupPrimaryClusterId

* Description: (Required) The Replication Group Primary Cluster ID.
* Type: String

### AutomationAssumeRole:

* Description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf.
* Type: String


## Details of SSM Document steps:

1. `RecordStartTime`
    * Type: aws:executeScript
    * Inputs: none
    * Outputs:
        * `StartStepTime`: The timestamp when the step execution started
    * Explanation:
        * Get the current time to start the elasticache replication group promote replica

1. `GetReplicationGroupMultiAZandAutomaticFailoverStatus`
    * Type: aws:executeAwsApi
    * Inputs:
        * `Service`: elasticache
        * `Api`: DescribeReplicationGroups
        * `ReplicationGroupId`: pass ReplicationGroupId parameter
    * Outputs:
        * `ReplicationGroupMultiAZ`: The elasticache replication group MultiAZ status
        * `ReplicationGroupAutomaticFailover`: The elasticache replication group AutomaticFailover status
    * Explanation:
        * Get the elasticache replication group MultiAZ and AutomaticFailover statuses.[describe_replication_groups](https://docs.aws.amazon.com/AmazonElastiCache/latest/APIReference/API_DescribeReplicationGroups.html) method

1. `ReplicationGroupMultiAZandAutomaticFailoverStatus`
    * Type: aws:branch
    * Inputs:
        * `ReplicationGroupMultiAZ`: pass the `ReplicationGroupMultiAZ` value from the previous step
        * `ReplicationGroupAutomaticFailover`: pass the `ReplicationGroupAutomaticFailover` value from the previous step
    * Outputs: none
    * Default: Go to the step `DisableReplicationGroupMultiAZandAutomaticFailover`
    * Explanation:
        * If `ReplicationGroupMultiAZ` is enabled, go to the step `DisableReplicationGroupMultiAZandAutomaticFailover`.
        * Else if, `ReplicationGroupMultiAZ` and `ReplicationGroupAutomaticFailover` are disabled, go to the step `PromoteReplicationGroupReplica`
    * isEnd: true

1. `DisableReplicationGroupMultiAZandAutomaticFailover`
    * Type: aws:executeAwsApi
    * Inputs:
        * `Service`: elasticache
        * `Api`: ModifyReplicationGroup
        * `ReplicationGroupId`: pass ReplicationGroupId parameter
        * `MultiAZEnabled`: needs to be equal to false
        * `AutomaticFailoverEnabled`: needs to be equal to false
        * `ApplyImmediately`: needs to be equal to true
    * Outputs:
        * `ActualReplicationGroupMultiAZ`: The current elasticache replication group MultiAZ parameter status
        * `ActualReplicationGroupAutomaticFailover`: The current elasticache replication group AutomaticFailover parameter status
    * Explanation:
        * Disable the elasticache replication group MultiAZ and AutomaticFailover parameters.[modify_replication_group](https://docs.aws.amazon.com/AmazonElastiCache/latest/APIReference/API_ModifyReplicationGroup.html) method
    * OnFailure: Go to step `RestoreReplicationGroupMultiAZandAutomaticFailover`

1. `VerifyReplicationGroupStatusAfterDisableReplicationGroupMultiAZandAutomaticFailover`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `Service`: elasticache
        * `Api`: DescribeReplicationGroups
        * `ReplicationGroupId`: pass ReplicationGroupId parameter
        * `PropertySelector`: use the $.ReplicationGroups[0].Status selector
        * `DesiredValues`: needs to be in available status
    * Explanation:
        * Wait for the elasticache updated replication group to be in available. [describe_replication_groups](https://docs.aws.amazon.com/AmazonElastiCache/latest/APIReference/API_DescribeReplicationGroups.html) method
        * Use the shared SSM Document as the step to avoid duplicates.
    * OnFailure: Go to step `RestoreReplicationGroupMultiAZandAutomaticFailover`

1. `PromoteReplicationGroupReplica`
    * Type: aws:executeAwsApi
    * Inputs:
        * `Service`: elasticache
        * `Api`: ModifyReplicationGroup
        * `ReplicationGroupId`: pass ReplicationGroupId parameter
        * `PrimaryClusterId`: pass ReplicationGroupPrimaryClusterId parameter
        * `ApplyImmediately`: needs to be equal to true
    * Outputs: none
    * Explanation:
        * Modify the elasticache replication group to promote a replica.[modify_replication_group](https://docs.aws.amazon.com/AmazonElastiCache/latest/APIReference/API_ModifyReplicationGroup.html) method
    * OnFailure: Go to step `RestoreReplicationGroupMultiAZandAutomaticFailover`

1. `VerifyReplicationGroupStatusAfterPromoteReplicationGroupReplica`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `Service`: elasticache
        * `Api`: DescribeReplicationGroups
        * `ReplicationGroupId`: pass ReplicationGroupId parameter
        * `PropertySelector`: use the $.ReplicationGroups[0].Status selector
        * `DesiredValues`: needs to be in available status
    * Explanation:
        * Wait for the elasticache updated replication group to be in available. [describe_replication_groups](https://docs.aws.amazon.com/AmazonElastiCache/latest/APIReference/API_DescribeReplicationGroups.html) method
        * Use the shared SSM Document as the step to avoid duplicates.
    * OnFailure: Go to step `RestoreReplicationGroupMultiAZandAutomaticFailover`

1. `RestoreReplicationGroupMultiAZandAutomaticFailover`
    * Type: aws:executeAwsApi
    * Inputs:
        * `Service`: elasticache
        * `Api`: ModifyReplicationGroup
        * `MultiAZEnabled`: pass the `ReplicationGroupMultiAZ` value from the `GetReplicationGroupMultiAZandAutomaticFailoverStatus` step
        * `AutomaticFailoverEnabled`: pass the `ReplicationGroupAutomaticFailover` value from the `GetReplicationGroupMultiAZandAutomaticFailoverStatus` step
        * `ApplyImmediately`: needs to be equal to true
    * Outputs: none
    * Explanation:
        * Modify the elasticache replication group to promote a replica.[modify_replication_group](https://docs.aws.amazon.com/AmazonElastiCache/latest/APIReference/API_ModifyReplicationGroup.html) method

1. `VerifyReplicationGroupStatusAfterRestoreReplicationGroupMultiAZandAutomaticFailover`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `Service`: elasticache
        * `Api`: DescribeReplicationGroups
        * `ReplicationGroupId`: pass ReplicationGroupId parameter
        * `PropertySelector`: use the $.ReplicationGroups[0].Status selector
        * `DesiredValues`: needs to be in available status
    * Explanation:
        * Wait for the elasticache updated replication group to be in available. [describe_replication_groups](https://docs.aws.amazon.com/AmazonElastiCache/latest/APIReference/API_DescribeReplicationGroups.html) method
        * Use the shared SSM Document as the step to avoid duplicates.

1. `GetReplicationGroupReplicaStatus`
    * Type: aws:executeAwsApi
    * Inputs:
        * `Service`: elasticache
        * `Api`: DescribeReplicationGroups
        * `ReplicationGroupId`: pass ReplicationGroupId parameter
    * Outputs:
        * `ReplicationGroupMultiAZ`: The elasticache replication group MultiAZ status
        * `ReplicationGroupAutomaticFailover`: The elasticache replication group AutomaticFailover status
    * Explanation:
        * Get the elasticache replication group MultiAZ and AutomaticFailover statuses.[describe_replication_groups](https://docs.aws.amazon.com/AmazonElastiCache/latest/APIReference/API_DescribeReplicationGroups.html) method

1. `GetReplicationGroupReplicaCurrentRole`
    * Type: aws:executeScript
    * Inputs:
        * `PrimaryClusterId`: pass ReplicationGroupPrimaryClusterId parameter
    * Outputs:
        * `ReplicaCurrentRole`: The current role of the replica node (PrimaryClusterId) : primary or replica
    * Explanation:
        * Get the current role of the replica node designated by the `PrimaryClusterId` input value. [describe_replication_groups](https://docs.aws.amazon.com/AmazonElastiCache/latest/APIReference/API_DescribeReplicationGroups.html) method

1. `OutputRecoveryTime`
    * Type: aws:executeScript
    * Inputs:
        * `StartStepTime`: pass `StartStepTime` value from the `RecordStartTime` step
    * Outputs:
        * `RecoveryTime`: The time difference between the first step and last step for the promote replica.
    * Explanation:
        * Calculate the time difference it takes to perform the elasticache replication group promote replica.

## Outputs

* `GetReplicationGroupMultiAZandAutomaticFailoverStatus.ReplicationGroupMultiAZ`: The elasticache replication group MultiAZ status
* `GetReplicationGroupMultiAZandAutomaticFailoverStatus.ReplicationGroupAutomaticFailover`: The elasticache replication group AutomaticFailover status
* `DisableReplicationGroupMultiAZandAutomaticFailover.ActualReplicationGroupMultiAZ`: The actual elasticache replication group MultiAZ status
* `DisableReplicationGroupMultiAZandAutomaticFailover.ActualReplicationGroupAutomaticFailover`: The actual elasticache replication group AutomaticFailover status
* `GetReplicationGroupReplicaCurrentRole.ReplicaCurrentRole`: The current role of the replica node
* `OutputRecoveryTime.RecoveryTime`: The time difference between the first step and last step for the promote replica
