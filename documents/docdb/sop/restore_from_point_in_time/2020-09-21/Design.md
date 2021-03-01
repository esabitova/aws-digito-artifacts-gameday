# Id
docdb:sop:restore_from_point_in_time:2020-09-21

## Intent
Used to restore a database to an old stable state from a Point in Time snapshot

## Type
Software Outage SOP

## Risk
Small

## Requirements
* Available DocumentDB Cluster

## Permission required for AutomationAssumeRole
* rds:CreateDBInstance
* rds:DescribeDBClusters
* rds:DescribeDBInstances
* rds:ModifyDBCluster
* rds:ModifyDBInstance
* rds:RestoreDBClusterToPointInTime

## Supports Rollback
No.

## Inputs
### DBClusterIdentifier:
* type: String
* description: (Required) DocDb Cluster Identifier
### RestoreToDate:
* type: String
* description: (Optional) Enter the available Point-in-Time date in UTC timezone following the pattern YYYY-MM-DDTHH:MM:SSZ
* default: 'latest'
### AutomationAssumeRole:
* type: String
* description: 
    (Optional) The ARN of the role that allows Automation to perform
    the actions on your behalf. If no role is specified, Systems Manager Automation
    uses your IAM permissions to run this document.
    default: ''

## Outputs
* OutputRecoveryTime.RecoveryTime
* GetRecoveryPoint.RecoveryPoint
* BackupDbClusterMetadata.BackupDbClusterInstancesCountValue
* BackupDbClusterMetadata.BackupDbClusterSecurityGroupsId
* BackupDbClusterInstancesMetadata.DBClusterInstancesMetadata
* RestoreClusterToPointInTime.RestoredClusterIdentifier
* RestoreDocDbClusterInstances.RestoredInstancesIdentifiers

## Details of SSM Document steps:
1. `RecordStartTime`
   * Type: aws:executeScript
   * Outputs:
      * `StartTime`
   * Explanation:
      * Start the timer when SOP starts
1. `GetRecoveryPoint`
   * Type: aws:executeScript
   * Inputs:
      * `DBClusterIdentifier`
      * `RestoreToDate`
   * Outputs:
      * `RecoveryPoint`: Default latest restorable time
   * Explanation:
      * Provides output with latest restorable time
1. `BackupDbClusterMetadata`
    * Type: aws:executeAwsApi
    * Inputs:
        * `DBClusterIdentifier`
    * Outputs:
      * `BackupDbClusterInstancesCountValue`: information about restorable cluster instances
      * `BackupDbClusterSecurityGroupsId`: security groups of the existing cluster
    * Explanation:
        * Backup information about provisioned Amazon DocumentDB cluster, by
          calling [DescribeDBClusters](https://docs.aws.amazon.com/documentdb/latest/developerguide/API_DescribeDBClusters.html)
1. `BackupDbClusterInstancesMetadata`
   * Type: aws:executeScript
   * Inputs:
      * `DBClusterIdentifier`
      * `BackupDbClusterMetadata.BackupDbClusterInstancesCountValue`
   * Outputs: `DBClusterInstancesMetadata`: provides detailed information about restorable cluster instances, like DBInstanceClass, Engine, AvailabilityZone
   * Explanation:
      * Backup detailed information about provisioned Amazon DocumentDB cluster instances, e.g. instance type and engine by
        calling [DescribeDBInstances](https://docs.aws.amazon.com/documentdb/latest/developerguide/API_DescribeDBInstances.html)
1. `RestoreClusterToPointInTime`
    * Type: aws:executeScript
    * Inputs:
      * `DBClusterIdentifier`
      * `RestoreToDate`
      * `BackupDbClusterMetadata.BackupDbClusterSecurityGroupsId`
    * Outputs:
        * `RestoredClusterIdentifier`: Identifier of a restored cluster
    * Explanation:
        * Set temporary restored cluster name by concatenation restorable cluster identifier `DBClusterIdentifier` and the suffix '-restored', because the clusters must have unique identifier at the same time
        * Check `RestoreToDate` value, if it has default 'latest' value,
          then call [restore_db_cluster_to_point_in_time](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/docdb.html#DocDB.Client.restore_db_cluster_to_point_in_time) method with the parameter `UseLatestRestorableTime=True`, or restore to the date from `RestoreToDate`. During API call security groups are passed as the parameter `VpcSecurityGroupIds` to request.
1. `RestoreDocDbClusterInstances`
    * Type: aws:executeScript
    * Inputs:
        * `BackupDbClusterMetadata.BackupDbClusterInstancesCountValue`
        * `RestoreClusterToPointInTime.RestoredClusterIdentifier`
        * `BackupDbClusterInstancesMetadata.DBClusterInstancesMetadata`
    * Outputs: `RestoredInstancesIdentifiers`: Identifiers of the restored cluster instances
    * Explanation:
       * Get information about restorable cluster instances from `BackupDbClusterInstancesCountValue`
       * Set PromotionTier and create cluster instances in the according order to match Primary and Replica instances by 
          calling [create_db_instance](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/docdb.html#DocDB.Client.create_db_instance) method. The values from `BackupDbClusterInstancesMetadata.DBClusterInstancesMetadata`, e.g. `AvailabilityZone`, `Engine` are passed as the parameters to request.
1. `RenameReplacedDocDbCluster`
    * Type: aws:executeScript
    * Inputs:
        * `DBClusterIdentifier`
    * Outputs: `ReplacedClusterIdentifier`: Identifier of the replaced cluster
    * Explanation:
        * Set restorable cluster identifier by concatenation restorable cluster identifier `DBClusterIdentifier` and the suffix '-replaced', because the clusters must have unique identifier at the same time
        * Call API method [modify_db_cluster](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/docdb.html#DocDB.Client.modify_db_cluster) and pass new restorable cluster identifier
1. `WaitUntilReplacedInstancesAvailable`
   * Type: aws:waitForAwsResourceProperty
   * Inputs:
      * `RenameReplacedDocDbCluster.ReplacedClusterIdentifier`: Restored cluster identifier
   * PropertySelector: `$.DBInstances..DBInstanceStatus`
   * Explanation:
      * Wait until replaced cluster instances become available
1. `RenameReplacedDocDbInstances`
    * Type: aws:executeScript
    * Inputs:
        * `RenameReplacedDocDbCluster.ReplacedClusterIdentifier`: Replaced cluster identifier
        * `BackupDbClusterMetadata.BackupDbClusterInstancesCountValue`: information about restorable cluster instances 
    * Outputs: `ReplacedInstancesIdentifiers`: Identifiers of the replaced cluster instances
    * Explanation:
        * Rename restored cluster instances by concatenation restorable cluster intances identifiers and the suffix '-replaced', because the cluster instances must have unique identifier at the same time
        * Call API method [modify_db_instance](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/docdb.html#DocDB.Client.modify_db_instance) and pass new restored cluster instances identifiers
1. `WaitUntilRestoredInstancesAvailable`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `RestoreClusterToPointInTime.RestoredClusterIdentifier`: Restored cluster identifier
    * PropertySelector: `$.DBInstances..DBInstanceStatus`
    * Explanation:
        * Wait until restored cluster instances become available
1. `RenameRestoredDocDbInstances`
    * Type: aws:executeScript
    * Inputs:
        * `RestoreDocDbClusterInstances.RestoredInstancesIdentifiers`: Restored cluster instances identifiers
        * `RestoreClusterToPointInTime.RestoredClusterIdentifier`: Restored cluster identifier
    * Outputs: `RestoredInstancesIdentifiers`: New identifiers of the restored cluster instances
    * Explanation:
        * Rename restored cluster instances by removing '-restored' suffix to match initial identifiers
        * Call API method [modify_db_instance](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/docdb.html#DocDB.Client.modify_db_instance) and pass initial cluster instances identifiers
1. `RenameRestoredCluster`
    * Type: aws:executeAwsApi
    * Inputs:
        * `RestoreClusterToPointInTime.RestoredClusterIdentifier`: Restored cluster identifier
        * `DBClusterIdentifier`: Initial cluster identifier
    * Explanation:
        * Rename restored cluster by removing '-restored' suffix to match initial identifier
        * Call API method and pass initial cluster identifier [ModifyDBCluster](https://docs.aws.amazon.com/documentdb/latest/developerguide/API_ModifyDBCluster.html)
1. `WaitForRenamedClusterId`
   * Type: aws:sleep
   * Inputs:
      * `Duration`: 10 seconds
   * Explanation:
   * * API calls require a DocDb cluster identifier to pass, and after renaming the identifier it will take some time to use one of them. `aws:waitForAwsResourceProperty` cannot be used here because it also requires the exact cluster ID as input.
1. `WaitUntilRenamedInstancesAvailable`
   * Type: aws:waitForAwsResourceProperty
   * Inputs:
      * `DBClusterIdentifier`: Restored cluster identifier
   * PropertySelector: `$.DBInstances..DBInstanceStatus`
   * Explanation:
      * Wait until renamed cluster instances become available
1. `OutputRecoveryTime`
   * Type: aws:executeScript
   * Inputs:
     * `RecordStartTime.StartTime`
   * Outputs:
      * `RecoveryTime`
   * Explanation:
      * Measures recovery time