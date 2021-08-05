# Id
elasticache:sop:redis_create_cache_cluster_from_snapshot:2020-10-26

## Intent
Create ElastiCache Replication Group from snapshot

## Type
Software Outage SOP

## Risk
Small

## Requirements
* ElastiCache Replication Group Snapshot

## Permission required for AutomationAssumeRole

* elasticache:CreateReplicationGroup
* elasticache:DescribeReplicationGroups

## Supports Rollback
No.

## Inputs

### TargetReplicationGroupId

* Description: (Required) The New Replication Group ID
* Type: String

### SourceSnapshotName

* Description: (Required) The ElastiCache Replication Group Snapshot Name.
* Type: String

### AutomationAssumeRole:

* Description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf.
* Type: String

### ReplicationGroupDescription

* Description: (Optional) The Replication Group Description
* Type: String
* Default: 'Replication Group From Snapshot'


## Details of SSM Document steps:

1. `RecordStartTime`
    * Type: aws:executeScript
    * Inputs: none
    * Outputs:
        * `StartStepTime`: The timestamp when the step execution started
    * Explanation:
        * Get the current time to start for creation of replication group from snapshot

1. `DescribeSnapshot`
    * Type: aws:executeScript
    * Inputs:
        * `SnapshotName`: pass SourceSnapshotName parameter
    * Outputs:
        * `RecoveryPoint`: $.Snapshots[0].NodeSnapshots[0].SnapshotCreateTime
        * `Settings`: JSON serialized dictionary with settings from source cluster if exists
    * Explanation:
        * Describe the snapshot and get source ReplicationGroupId then try to see if the source database is present and
          if yes, we copy settings from there.
1. `CreateReplicationGroupFromSnapshot`
    * Type: aws:executeScript
    * Inputs:
        * `ReplicationGroupId`: pass TargetReplicationGroupId parameter
        * `ReplicationGroupDescription`: pass ReplicationGroupDescription parameter
        * `SnapshotName`: pass SourceSnapshotName parameter
        * `Settings`: pass DescribeSnapshot.Settings
    * Outputs:
        * `ReplicationGroupARN`: The elasticache new replication group ARN
    * Explanation:
        * Create a new elasticache replication group from an existing snapshot.

1. `VerifyReplicationGroupStatusAfterCreateReplicationGroupFromSnapshot`
   * Type: aws:waitForAwsResourceProperty
   * Inputs:
      * `Service`: elasticache
      * `Api`: DescribeReplicationGroups
      * `ReplicationGroupId`: pass TargetReplicationGroupId parameter
      * `PropertySelector`: use the $.ReplicationGroups[0].Status selector
      * `DesiredValues`: needs to be in available status
   * Explanation:
      * Wait for the elasticache new replication group to be in available [describe_replication_groups](https://docs.aws.amazon.com/AmazonElastiCache/latest/APIReference/API_DescribeReplicationGroups.html) method
      * Use the shared SSM Document as the step to avoid duplicates.

1. `OutputRecoveryTime`
   * Type: aws:executeScript
   * Inputs:
      * `StartStepTime`: pass `StartStepTime` value from the `RecordStartTime` step
   * Outputs:
      * `RecoveryTime`: The time difference between the first step and last step for to create replication group from snapshot
   * Explanation:
      * Calculate the time difference it takes to perform the elasticache replication group  create replication group from snapshot

## Outputs

* `CreateReplicationGroupFromSnapshot.ReplicationGroupARN`: The elasticache new replication group ARN
* `OutputRecoveryTime.RecoveryTime`: The time difference between the first step and last step to create replication
  group from snapshot
* `DescribeSnapshot.RecoveryPoint`: Recovery point based on the timestamp on the snapshot

