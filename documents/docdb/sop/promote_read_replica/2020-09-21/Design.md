# Id
docdb:sop:promote_read_replica:2020-09-21

## Intent
Used to switch database to a read replica

## Type
Software Outage SOP

## Risk
Medium

## Requirements
* Available DocumentDB Cluster

## Permission required for AutomationAssumeRole
* rds:DescribeDBClusters
* rds:FailoverDBCluster

## Supports Rollback
No.

## Inputs
### DBClusterIdentifier:
* type: String
* description: (Required) DocDb Cluster Identifier
### DBInstanceReplicaIdentifier:
* type: String
* (Required) DocDb Replica Identifier
### AutomationAssumeRole:
* type: String
* description: 
    (Optional) The ARN of the role that allows Automation to perform
    the actions on your behalf. If no role is specified, Systems Manager Automation
    uses your IAM permissions to run this document.
    default: ''
## Outputs
* OutputRecoveryTime.RecoveryTime

## Details of SSM Document steps:
1. `RecordStartTime`
    * Type: aws:executeScript
    * Outputs:
        * `StartTime`
    * Explanation:
        * Start the timer when SOP starts
1. `PromoteReadReplica`
   * Type: aws:executeAwsApi
   * Inputs:
      * `DBClusterIdentifier`
      * `DBInstanceReplicaIdentifier`
   * Explanation:
      * Promotes Read Replica to Primary instance by
        calling [FailoverDBCluster](https://docs.aws.amazon.com/documentdb/latest/developerguide/API_FailoverDBCluster.html) 
1. `WaitUntilClusterAvailable`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `DBClusterIdentifier`: DocDB cluster identifier
    * PropertySelector: `$.DBClusters[0].Status`
    * Explanation:
        * Wait until cluster state become available
1. `OutputRecoveryTime`
    * Type: aws:executeScript
    * Inputs:
        * `RecordStartTime.StartTime`
    * Outputs:
        * `RecoveryTime`
    * Explanation:
        * Measures recovery time