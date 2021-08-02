# Id
elasticache:sop:redis-increase-shards:2020-10-26

## Intent

Increase shards in the cluster

## Type

Software Outage SOP, AZ

## Risk

Small

## Requirements
* ElastiCache Redis replication group (cluster mode enabled)

## Permission required for AutomationAssumeRole

* elasticache:ModifyReplicationGroupShardConfiguration
* elasticache:DescribeReplicationGroups

## Supports Rollback
No.

## Inputs

### ReplicationGroupId

* Description: (Required) The ElastiCache Replication Group ID.
* Type: String

### NewShardCount

* Description: (Required) The number of node groups (shards).
* Type: Integer

### NewReshardingConfiguration:

* description: >-
  (Optional) The preferred availability zones for each node group in the cluster by order, e.g. ["PreferredAvailabilityZones":["eu-west-3a"]}]. If it is [] then ElastiCache will select
  availability zones for you.
* type: MapList
* default: []

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
        * Get the current time to start the elasticache replication group resharding

1. `VerifyReplicationGroupAvailableStatusBeforeModification`
    * Type: aws:waitForAwsResourceProperty
    * timeoutSeconds: 2400
    * Inputs:
        * `Service`: elasticache
        * `Api`: DescribeReplicationGroups
        * `ReplicationGroupId`: pass ReplicationGroupId parameter
        * `PropertySelector`: use the $.ReplicationGroups[0].Status selector
        * `DesiredValues`: needs to be in available status
    * Explanation:
        * Wait for the elasticache updated replication group to be in
          available. [describe_replication_groups](https://docs.aws.amazon.com/AmazonElastiCache/latest/APIReference/API_DescribeReplicationGroups.html) method
        * Use the shared SSM Document as the step to avoid duplicates.

1. `ModifyReplicationGroupShardConfiguration`
    * Type: aws:executeAwsApi
    * timeoutSeconds: 2400
    * Inputs:
        * `Service`: elasticache
        * `Api`: ModifyReplicationGroupShardConfiguration
        * `ReplicationGroupId`: pass ReplicationGroupId parameter
        * `NodeGroupCount`: pass NewShardCount parameter
        * `ApplyImmediately`: needs to be true
        * `ReshardingConfiguration`: '{{NewReshardingConfiguration}}'
    * Outputs:
      * `ReplicationGroupStatus`: The elasticache replication group status
   * Explanation:
      * Modify the elasticache replication group node groups count (shards).[modify_replication_group_shard_configuration](https://docs.aws.amazon.com/AmazonElastiCache/latest/APIReference/API_ModifyReplicationGroupShardConfiguration.html) method

1. `VerifyReplicationGroupStatusAfterModifyReplicationGroupShardConfiguration`
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
      * `RecoveryTime`: The time difference between the first step and last step for the resharding.
   * Explanation:
      * Calculate the time difference it takes to perform the elasticache replication group resharding

## Outputs

* `OutputRecoveryTime.RecoveryTime`: The time difference between the first step and last step for the resharding