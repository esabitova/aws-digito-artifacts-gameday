# Id
elasticache:sop:redis_change_reserved_memory:2020-10-26

## Intent
Scale up Redis cluster by changing the percentage of non-data memory that is used for backup and failover

## Type
Software Outage SOP

## Risk
Medium

## Requirements
* ElastiCache Redis cluster


## Permission required for AutomationAssumeRole

* elasticache:ModifyReplicationGroupShardConfiguration
* elasticache:DescribeReplicationGroups
* elasticache:ModifyReplicationGroup
* elasticache:ModifyCacheParameterGroup
* elasticache:CreateCacheParameterGroup

## Supports Rollback
No.

## Inputs

### ReplicationGroupId

* Description: (Required) The ElastiCache Replication Group ID.
* Type: String

### CustomCacheParameterGroupName

* Description: (Required) A Custom Cache Parameter Group Name.
* Type: String

### CustomCacheParameterGroupFamily

* Description: (Required) A Custom Cache Parameter Group Family.
* Type: String

### CustomCacheParameterGroupDescription

* Description: (Optional) A Custom Cache Parameter Group Description.
* Type: String
* Default: "Cache Parameter Group For Reserved Memory created by SSM document Digito-RedisScaleUp_2020-10-26"

### ReservedMemoryPercent

* Description: (Required) Parameters to Manage Reserved Memory.
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
      * Get the current time to start the elasticache memory change

1. `GetCustomCacheParameterGroupStatus`
   * Type: aws:executeScript
   * Inputs:
      * `CacheParameterGroupName`: pass CustomCacheParameterGroupName parameter
   * Outputs:
      * `CacheParameterGroupExist`: Whether the custom cache parameter group exists (true) or not (false)
   * Explanation:
      * Check whether the custom cache parameter group exists or not.[describe_cache_parameter_groups](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/elasticache.html#ElastiCache.Client.describe_cache_parameter_groups) method

1. `CheckCustomCacheParameterGroupStatus`
   * Type: aws:branch
   * Inputs:
      * `CacheParameterGroupExist`: pass the `CacheParameterGroupExist` value from the previous step
   * Outputs: none
   * Explanation:
      * If `CacheParameterGroupExist` is true, go to the step `ModifyCacheParameterGroup`.
      * If `CacheParameterGroupExist` is false, go to the step `CreateCacheParameterGroup`

1. `CreateCacheParameterGroup`
   * Type: aws:executeAwsApi
   * Inputs:
      * `Service`: elasticache
      * `Api`: CreateCacheParameterGroup
      * `CacheParameterGroupName`: pass CustomCacheParameterGroupName parameter
      * `CacheParameterGroupFamily`: pass CustomCacheParameterGroupFamily parameter
      * `Description`: pass CustomCacheParameterGroupDescription parameter
   * Outputs:
      * `CacheParameterGroupARN`: The custom cache parameter group arn
   * Explanation:
      * Create a custom cache parameter group.[create_cache_parameter_group](https://docs.aws.amazon.com/AmazonElastiCache/latest/APIReference/API_CreateCacheParameterGroup.html) method

1. `ModifyCacheParameterGroup`
   * Type: aws:executeAwsApi
   * Inputs:
      * `Service`: elasticache
      * `Api`: ModifyCacheParameterGroup
      * `CacheParameterGroupName`: pass CustomCacheParameterGroupName parameter
      * `ParameterNameValues`:
         - `ParameterName`: needs to be equal to "reserved-memory-percent"
           `ParameterValue`: pass ReservedMemoryPercent parameter
         - `ParameterName`: needs to be equal to "cluster-enabled"
           `ParameterValue`: needs to be equal to "yes"
   * Outputs: none
   * Explanation:
      * Modify the custom cache parameter group to use the "reserved-memory-percent" parameter.[modify_cache_parameter_group](https://docs.aws.amazon.com/AmazonElastiCache/latest/APIReference/API_ModifyCacheParameterGroup.html) method

1. `ModifyReplicationGroup`
   * Type: aws:executeAwsApi
   * Inputs:
      * `Service`: elasticache
      * `Api`: ModifyReplicationGroup
      * `ReplicationGroupId`: pass ReplicationGroupId parameter
      * `CacheParameterGroupName`: pass CustomCacheParameterGroupName parameter
      * `ApplyImmediately`: needs to be equal to true
   * Outputs:
      * `ReplicationGroupStatus`: The elasticache replication group status
   * Explanation:
      * Modify the elasticache replication group to use the custom cache parameter group with the "reserved-memory-percent" parameter.[modify_replication_group](https://docs.aws.amazon.com/AmazonElastiCache/latest/APIReference/API_ModifyReplicationGroup.html) method

1. `VerifyReplicationGroupStatusAfterModifyReplicationGroup`
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
      * `RecoveryTime`: The time difference between the first step and last step for the memory change.
   * Explanation:
      * Calculate the time difference it takes to perform the elasticache memory change
## Outputs

* `GetCustomCacheParameterGroupStatus.CacheParameterGroupExist`: Whether the custom cache parameter group exists (true) or not (false)
* `ModifyReplicationGroup.ReplicationGroupStatus`: The elasticache replication group status
* `OutputRecoveryTime.RecoveryTime`: The time difference between the first step and last step for the memory change.
