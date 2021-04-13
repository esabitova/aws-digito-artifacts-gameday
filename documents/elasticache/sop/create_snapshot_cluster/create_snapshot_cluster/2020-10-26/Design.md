# Id
elasticache:sop:create_snapshot_cluster:2020-10-26

## Intent
Create manual backup for a cluster

## Type
Software Outage SOP 

## Risk
Medium

## Requirements
* An elasticache Cluster


## Permission required for AutomationAssumeRole

* elasticache:CreateSnapshot
* elasticache:DescribeSnapshots

## Supports Rollback
No.

## Inputs

### CacheClusterId

* Description: (Required) The ElastiCache Cluster ID.
* Type: String

### SnapshotName

* Description: (Required) The ElastiCache Cluster Snapshot Name.
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
        * Get the current time to start the elasticache cluster snapshot

1. `CreateElastiCacheClusterSnapshot`   
    * Type: aws:executeAwsApi
    * Inputs:
        * `Service`: elasticache
        * `Api`: CreateSnapshot
        * `CacheClusterId`: pass CacheClusterId parameter
        * `SnapshotName`: pass SnapshotName parameter
    * Outputs:
        * `SnapshotArn`: The elasticache cluster snapshot ARN
    * Explanation:
        * Get the elasticache cluster snapshot ARN. [create_snapshot](https://docs.aws.amazon.com/AmazonElastiCache/latest/APIReference/API_CreateSnapshot.html) method

1. `VerifySnapshotStatusAfterCreateElastiCacheClusterSnapshot`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `Service`: elasticache
        * `Api`: DescribeSnapshots
        * `CacheClusterId`: pass CacheClusterId parameter
        * `SnapshotName`: pass SnapshotName parameter
        * `PropertySelector`: use the $.Snapshots[0].SnapshotStatus selector
        * `DesiredValues`: needs to be in available status 
    * Explanation:
        * Wait for the  elasticache cluster snapshot to be in available status after the snaphot creation is completed. [describe_snaphots](https://docs.aws.amazon.com/AmazonElastiCache/latest/APIReference/API_DescribeSnapshots.html) method
        * Use the shared SSM Document as the step to avoid duplicates. 

1. `OutputRecoveryTime`
    * Type: aws:executeScript
    * Inputs:
        * `StartStepTime`: pass `StartStepTime` value from the `RecordStartTime` step
    * Outputs:
        * `RecoveryTime`: The time difference between the first step and last step for the snapshot.
    * Explanation:
        * Calculate the time difference it takes to perform the elasticache cluster snapshot 

## Outputs

* `CreateElastiCacheClusterSnapshot.SnapshotArn`: The elasticache cluster snapshot ARN
* `OutputRecoveryTime.RecoveryTime`: The elasticache cluster snapshot ARN