# Id
docdb:sop:scaling_up:2020-09-21

## Intent
Used to scale up the cluster has above the threshold utilization

## Type
Software Outage SOP

## Risk
Small

## Requirements
* Available DocumentDB Cluster

## Permission required for AutomationAssumeRole
* rds:DescribeDBClusters
* rds:DescribeDBInstances
* rds:CreateDBInstance

## Supports Rollback
No.

## Inputs
### DBClusterIdentifier:
* type: String
* description: (Required) DocDb Cluster Identifier
### DBInstanceReplicaIdentifier:
* type: String
* description: (Required) DocDb Replica Identifier
### AvailabilityZone:
* type: String
* description: (Required) DocDb availability zone to place the instance
### AutomationAssumeRole:
* type: String
* description: 
    (Optional) The ARN of the role that allows Automation to perform
    the actions on your behalf. If no role is specified, Systems Manager Automation
    uses your IAM permissions to run this document.
    default: ''

## Outputs
* `BackupDbInstancesMetadata.BackupDbClusterInstancesCountValue`: cluster instances metadata
* `BackupDbClusterInstancesCount.DbClusterInstancesNumber`: initial cluster instances number
* `AddDocDbReadReplica.CurrentDbClusterInstancesCountValue`: number of instances after scaling up
* `OutputRecoveryTime.RecoveryTime`: recovery time in seconds

## Details of SSM Document steps:
1. `RecordStartTime`
    * Type: aws:executeScript
    * Outputs:
        * `StartTime`
    * Explanation:
        * Start the timer when SOP starts
1. `BackupDbInstancesMetadata`
   * Type: aws:executeAwsApi
   * Inputs:
       * `DBClusterIdentifier`
   * Outputs:
       * `BackupDbClusterInstancesCountValue`: information about restorable cluster instances
   * Explanation:
       * Backup information about provisioned Amazon DocumentDB cluster, by
         calling [DescribeDBClusters](https://docs.aws.amazon.com/documentdb/latest/developerguide/API_DescribeDBClusters.html)
1. `BackupDbClusterInstancesCount`
   * Type: aws:executeScript
   * Inputs:
      * `BackupDbInstancesMetadata.BackupDbClusterInstancesCountValue`
   * Outputs:
      * `DbClusterInstancesNumber`: Number of existing instances before scaling up
   * Explanation:
       * Counts number of the existing instances
1. `AddDocDbReadReplica`
    * Type: aws:executeAwsApi
    * Inputs:
        * `AvailabilityZone`
        * `DBInstanceReplicaIdentifier`: identifier of the instance, that will be added
        * `DBClusterIdentifier`
        * `DBInstanceClass`
        * `Engine`
    * Explanation:
        * Adjust size of the cluster by changing a number of nodes adding one Read Replica by
          calling [CreateDBInstance](https://docs.aws.amazon.com/documentdb/latest/developerguide/API_CreateDBInstance.html)
1. `WaitUntilInstancesAvailable`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `DBClusterIdentifier`
    * PropertySelector: `$.DBInstances..DBInstanceStatus`
    * Explanation:
        * Wait until cluster instances become available
1. `VerifyCurrentInstancesCount`
    * Type: aws:executeScript
    * Inputs:
        * `BackupDbClusterInstancesCount.DbClusterInstancesNumber`: initial cluster instances number
        * `DBClusterIdentifier`
   * Outputs:
        * `CurrentInstancesNumber`
    * Explanation:
        * Receives DocDb cluster metadata by API call and counts current instances number. Compares initial and current instances number, current number value must be greater then the initial one. API action: [DescribeDBClusters](https://docs.aws.amazon.com/documentdb/latest/developerguide/API_DescribeDBClusters.html)
1. `OutputRecoveryTime`
    * Type: aws:executeScript
    * Inputs:
        * `RecordStartTime.StartTime`
    * Outputs:
        * `RecoveryTime`
    * Explanation:
        * Measures recovery time
