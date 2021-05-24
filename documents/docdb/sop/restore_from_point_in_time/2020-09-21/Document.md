# Id
docdb:sop:restore_from_point_in_time:2020-09-21

## Document Type
Automation

## Description
Used to restore a database to an old stable state from a Point in Time snapshot.

## Disruption Type
SOFTWARE

## Risk
SMALL

## Permissions required
    * rds:CreateDBInstance
    * rds:DescribeDBClusters
    * rds:DescribeDBInstances
    * rds:ModifyDBCluster
    * rds:ModifyDBInstance
    * rds:RestoreDBClusterToPointInTime

## Depends On
None

## Inputs
### `DBClusterIdentifier`
    * type: String
    * description: (Required) DocDb Cluster Identifier
### `RestoreToDate`
    * type: String
    * description: (Optional) Enter the available Point-in-Time date in UTC timezone following the pattern YYYY-MM-DDTHH:MM:SSZ
### `AutomationAssumeRole`
    * type: String
    * description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf. If no role is specified, Systems Manager Automation uses your IAM permissions to run this document.

## Outputs
    * `OutputRecoveryTime.RecoveryTime`
    * `GetRecoveryPoint.RecoveryPoint`
    * `BackupDbClusterMetadata.BackupDbClusterInstancesCountValue`
    * `BackupDbClusterMetadata.BackupDbClusterSecurityGroupsId`
    * `BackupDbClusterInstancesMetadata.DBClusterInstancesMetadata`
    * `RestoreClusterToPointInTime.RestoredClusterIdentifier`
    * `RestoreDocDbClusterInstances.RestoredInstancesIdentifiers`
