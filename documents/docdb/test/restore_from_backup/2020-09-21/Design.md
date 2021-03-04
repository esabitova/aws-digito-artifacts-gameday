# Id
docdb:sop:restore_from_backup:2020-09-21

## Intent
Used to recover the database into a known good state

## Type
Software Outage SOP

## Risk
Medium

## Requirements
* Available DocumentDB Cluster

## Permission required for AutomationAssumeRole
* rds:CreateDBInstance
* rds:DescribeDBClusters
* rds:DescribeDBInstances
* rds:DescribeDBClusterSnapshots
* rds:ModifyDBCluster
* rds:ModifyDBInstanc
* rds:RestoreDBClusterFromSnapshot

## Supports Rollback
No.

## Inputs
### DBClusterIdentifier:
* type: String
* description: (Required) DocDb Cluster Identifier
### DBSnapshotIdentifier:
* type: String
* description: (Optional) DocDb Snapshot Identifier
* default: 'latest'

### AutomationAssumeRole:
* type: String
* description: 
    (Optional) The ARN of the role that allows Automation to perform
    the actions on your behalf. If no role is specified, Systems Manager Automation
    uses your IAM permissions to run this document.
    default: ''

## Outputs
* BackupDbClusterMetadata.BackupDbClusterInstancesCountValue
* BackupDbClusterInstancesMetadata.DBClusterInstancesMetadata
* GetLatestSnapshotIdentifier.LatestSnapshot
* GetLatestSnapshotIdentifier.LatestSnapshotEngine
* GetLatestSnapshotIdentifier.LatestClusterIdentifier
* RestoreDocDbCluster.RestoredClusterIdentifier
* RestoreDocDbClusterInstances.RestoredInstancesIdentifiers
* RenameReplacedDocDbCluster.ReplacedClusterIdentifier
* RenameReplacedDocDbInstances.ReplacedInstancesIdentifiers
* RenameRestoredDocDbInstances.RestoredInstancesIdentifiers
* OutputRecoveryTime.RecoveryTime

## Details of SSM Document steps:
1. `RecordStartTime`
    * Type: aws:executeScript
    * Outputs:
        * `StartTime`
    * Explanation:
        * Start the timer when SOP starts
1. `BackupDbClusterMetadata`
   * Type: aws:executeAwsApi
   * Inputs:
       * `DBClusterIdentifier`
   * Outputs:
       * `BackupDbClusterInstancesCountValue`: information about restorable cluster instances
   * Explanation:
       * Backup information about provisioned Amazon DocumentDB cluster, by
         calling [DescribeDBClusters](https://docs.aws.amazon.com/documentdb/latest/developerguide/API_DescribeDBClusters.html)
1. `BackupDbClusterInstancesMetadata`
   * Type: aws:executeScript
   * Inputs:
      * `DBClusterIdentifier`
      * `BackupDbClusterMetadata.BackupDbClusterInstancesCountValue`
   * Outputs:
      * `DBClusterInstancesMetadata`
   * Explanation:
      * Get information about existing cluster instances, e.g. `DBInstanceClass`, `Engine`, `AvailabilityZone` by calling [describe_db_instances](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/docdb.html#DocDB.Client.describe_db_instances)
1. `GetLatestSnapshotIdentifier`
   * Type: aws:executeScript
   * Inputs:
      * `DBClusterIdentifier`
   * Outputs:
        * `LatestSnapshot`
        * `LatestSnapshotEngine`
        * `LatestClusterIdentifier`
   * Explanation:
       * Gets information about latest snapshot and cluster identifier by calling [describe_db_cluster_snapshots](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/docdb.html#DocDB.Client.describe_db_cluster_snapshots)
1. `RestoreDocDbCluster`
    * Type: aws:executeScript
    * Inputs:
        * `DBClusterIdentifier`
        * `DBSnapshotIdentifier`
        * `GetLatestSnapshotIdentifier.LatestSnapshot`
        * `GetLatestSnapshotIdentifier.LatestSnapshotEngine`
    * Explanation:
        * Restores DocDb cluster using provided the snapshot identifier from input or using latest snapshot if the field DBSnapshotIdentifier has default value `latest` or is empty by calling [restore_db_cluster_from_snapshot](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/docdb.html#DocDB.Client.restore_db_cluster_from_snapshot)
1. `WaitForRenamedClusterId`
   * Type: aws:sleep
   * Inputs:
      * `Duration`: 10 seconds
   * Explanation:
      * API calls require a DocDb cluster identifier to pass, and after renaming the identifier it will take some time to use one of them. `aws:waitForAwsResourceProperty` cannot be used here because it also requires the exact cluster ID as input.
1. `WaitUntilClusterStateRunning`
   * Type: aws:waitForAwsResourceProperty
   * Inputs:
      * `RestoreDocDbCluster.RestoredClusterIdentifier`: Restored cluster identifier
   * PropertySelector: `$.DBClusters[0].Status`
   * Explanation:
      * Wait until renamed cluster become available
1. `RestoreDocDbClusterInstances`
    * Type: aws:executeScript
    * Inputs:
        * `BackupDbClusterMetadata.BackupDbClusterInstancesCountValue`: used to restore the same number of the cluster instances, as in initial cluster
        * `RestoreDocDbCluster.RestoredClusterIdentifier`
        * `BackupDbClusterInstancesMetadata.DBClusterInstancesMetadata`: provides `DBInstanceClass`, `Engine`, `AvailabilityZone` parameters for restored instances
   * Outputs:
        * `RestoredInstancesIdentifiers`
    * Explanation:
        * Create the same number of the cluster instances as in initial cluster. Restored cluster instances identifiers set by concatenation initial cluster instances identifiers and the suffix `-restored-from-backup`. API action: [create_db_instance](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/docdb.html#DocDB.Client.create_db_instance)
1. `RenameReplacedDocDbCluster`
    * Type: aws:executeScript
    * Inputs:
        * `DBClusterIdentifier`
    * Outputs:
        * `ReplacedClusterIdentifier`
    * Explanation:
        * Rename replaced cluster identifier by concatenation initial cluster identifier and the suffix '-replaced', because the clusters must have unique identifiers at the same time. API action: [modify_db_cluster](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/docdb.html#DocDB.Client.modify_db_cluster)
1. `RenameReplacedDocDbInstances`
    * Type: aws:executeScript
    * Inputs:
        * `RenameReplacedDocDbCluster.ReplacedClusterIdentifier`
        * `BackupDbClusterMetadata.BackupDbClusterInstancesCountValue`
    * Outputs:
        * `ReplacedInstancesIdentifiers`
    * Explanation:
        * Rename replaced cluster instances identifiers by concatenation initial instances identifiers and the suffix '-replaced', because the cluster instances must have unique identifiers at the same time. API action: [modify_db_instance](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/docdb.html#DocDB.Client.modify_db_instance)
1. `WaitUntilInstanceStateRunning`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `RestoreDocDbCluster.RestoredClusterIdentifier`
    * PropertySelector: `$.DBInstances..DBInstanceStatus`
   * Explanation:
       * Wait until renamed cluster instances become available
1. `RenameRestoredDocDbInstances`
    * Type: aws:executeScript
    * Inputs:
        * `RestoreDocDbClusterInstances.RestoredInstancesIdentifiers`
        * `RestoreDocDbCluster.RestoredClusterIdentifier`
    * Outputs:
        * `RestoredInstancesIdentifiers`
    * Explanation:
        * Rename restored cluster instances identifiers by removing the suffix `-restored-from-backup` to match initial instances identifiers. API action: [modify_db_instance](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/docdb.html#DocDB.Client.modify_db_instance)
1. `RenameRestoredCluster`
    * Type: aws:executeAwsApi
    * Inputs:
        * `RestoreDocDbCluster.RestoredClusterIdentifier`
        * `GetLatestSnapshotIdentifier.LatestClusterIdentifier`
    * Explanation:
        * Rename restored cluster identifier to identifier of the cluster in snapshot. API action: [ModifyDBCluster](https://docs.aws.amazon.com/documentdb/latest/developerguide/API_ModifyDBCluster.html)
1. `WaitUntilRestoredInstancesAvailable`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `DBClusterIdentifier`
    * PropertySelector: `$.DBInstances..DBInstanceStatus`
    * Explanation:
        * Wait until restored cluster instances become available
1. `OutputRecoveryTime`
    * Type: aws:executeScript
    * Inputs:
        * `RecordStartTime.StartTime`
    * Outputs:
        * `RecoveryTime`
    * Explanation:
        * Measures recovery time
