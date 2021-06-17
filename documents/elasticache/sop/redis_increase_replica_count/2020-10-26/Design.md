# Id
elasticache:sop:redis_increase_replica_count:2020-10-26

## Intent
Increase readonly replica count

## Type
Software Outage SOP

## Risk
Low

## Requirements
* Elasticache Redis cluster

## Permission required for AutomationAssumeRole

* elasticache:IncreaseReplicaCount
* elasticache:DescribeReplicationGroups

## Supports Rollback
No.

## Inputs

### ReplicationGroupId

* Description: (Required) The ElastiCache Replication Group ID.
* Type: String

### NewReplicaCount

* Description: (Required) The number of read replica nodes that you want.
* Type: Integer

### AutomationAssumeRole

* Description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf.
* Type: String

## Details of SSM Document steps:

1. `RecordStartTime`
   * Type: aws:executeScript
   * Inputs: none
   * Outputs:
      * `StartStepTime`: The timestamp when the step execution started
   * Explanation:
      * Get the current time to start the elasticache replication group increase replica count

1. `IncreaseReplicaCount`
   * Type: aws:executeAwsApi
   * Inputs:
      * `Service`: elasticache
      * `Api`: IncreaseReplicaCount
      * `ReplicationGroupId`: pass ReplicationGroupId parameter
      * `NewReplicaCount`: pass NewReplicaCount parameter
      * `ApplyImmediately`: needs to be true
   * Outputs:
      * `ReplicationGroupStatus`: The elasticache replication group status
   * Explanation:
      * Increase the elasticache replication group replicas.[increase_replica_count](https://docs.aws.amazon.com/AmazonElastiCache/latest/APIReference/API_IncreaseReplicaCount.html) method

1. `VerifyReplicationGroupStatusAfterIncreaseReplicaCount`
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

1. `OutputRecoveryTime`
   * Type: aws:executeScript
   * Inputs:
      * `StartStepTime`: pass `StartStepTime` value from the `RecordStartTime` step
   * Outputs:
      * `RecoveryTime`: The time difference between the first step and last step for the increase replica count.
   * Explanation:
      * Calculate the time difference it takes to perform the elasticache replication group  increase replica count.

## Outputs

* `IncreaseReplicaCount.ReplicationGroupStatus`: The elasticache replication group status
* `OutputRecoveryTime.RecoveryTime`: The time difference between the first step and last step for the increase replica count.
