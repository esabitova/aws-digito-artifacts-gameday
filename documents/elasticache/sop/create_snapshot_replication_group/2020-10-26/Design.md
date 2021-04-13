# Id
elasticache:sop:create_snapshot_replication_group:2020-10-26

## Intent
Create manual backup for a replication group

## Type
Software Outage SOP 

## Risk
Medium

## Requirements
* An elasticache Replication group


## Permission required for AutomationAssumeRole

* elasticache:CreateSnapshot
* elasticache:DescribeSnapshots

## Supports Rollback
No.

## Inputs

### ReplicationGroupId

* Description: (Required) The ElastiCache Replication Group ID. Conflict with CacheClusterId
* Type: String

### SnapshotName

* Description: (Required) The ElastiCache Replication Group Snapshot Name.
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
        * Get the current time to start the elasticache replication group snapshot

1. `CreateElastiCacheReplicationGroupSnapshot`   
    * Type: aws:executeAwsApi
    * Inputs:
        * `Service`: elasticache
        * `Api`: CreateSnapshot
        * `ReplicationGroupId`: pass ReplicationGroupId parameter
        * `SnapshotName`: pass SnapshotName parameter
    * Outputs:
        * `SnapshotArn`: The elasticache replication group snapshot ARN
    * Explanation:
        * Get the elasticache replication group snapshot ARN. [create_snapshot](https://docs.aws.amazon.com/AmazonElastiCache/latest/APIReference/API_CreateSnapshot.html) method

1. `VerifySnapshotStatusAfterCreateElastiCacheReplicationGroupSnapshot`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `Service`: elasticache
        * `Api`: DescribeSnapshots
        * `ReplicationGroupId`: pass ReplicationGroupId parameter
        * `SnapshotName`: pass SnapshotName parameter
        * `PropertySelector`: use the $.Snapshots[0].SnapshotStatus selector
        * `DesiredValues`: needs to be in available status 
    * Explanation:
        * Wait for the  elasticache replication group snapshot to be in available status after the snaphot creation is completed. [describe_snaphots](https://docs.aws.amazon.com/AmazonElastiCache/latest/APIReference/API_DescribeSnapshots.html) method
        * Use the shared SSM Document as the step to avoid duplicates. 

1. `OutputRecoveryTime`
    * Type: aws:executeScript
    * Inputs:
        * `StartStepTime`: pass `StartStepTime` value from the `RecordStartTime` step
    * Outputs:
        * `RecoveryTime`: The time difference between the first step and last step for the snapshot.
    * Explanation:
        * Calculate the time difference it takes to perform the elasticache replication group snapshot 

## Outputs

* `CreateElastiCacheReplicationGroupSnapshot.SnapshotArn`: The elasticache replication group snapshot ARN
* `OutputRecoveryTime.RecoveryTime`: The elasticache replication group snapshot ARN