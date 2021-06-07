# Id
docdb:sop:scaling_down:2020-09-21

## Intent
Used to scale down the cluster has below the threshold utilization

## Type
Software Outage SOP

## Risk
Small

## Requirements
* Available DocumentDB Cluster

## Permission required for AutomationAssumeRole
* rds:DescribeDBClusters
* rds:DeleteDBInstance

## Supports Rollback
No.

## Inputs
### DBClusterIdentifier:
* type: String
* description: (Required) DocDb Cluster Identifier
### DBInstanceReplicaIdentifier:
* type: String
* description: (Required) DocDb Replica Identifier
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
* `VerifyCurrentInstancesCount.CurrentInstancesNumber`: number of instances after scaling down

## Details of SSM Document steps:
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
      * `DbClusterInstancesNumber`: Number of existing instances before scaling down
   * Explanation:
      * Counts number of the existing instances
1. `VerifyInstanceExistInCluster`
    * Type: aws:executeScript
    * Inputs:
        * `DBInstanceReplicaIdentifier`
        * `DBClusterIdentifier`
    * Explanation:
        * Verifies the cluster instance exists in the cluster. When the exception message contains `DBInstanceNotFound` raises the custom exception `Cluster instance {events['DBInstanceIdentifier']} is not found in cluster {events['DBClusterIdentifier']` or raises other exception. API action: [describe_db_instances](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/docdb.html#DocDB.Client.describe_db_instances)
1. `RemoveDocDbReadReplica`
    * Type: aws:executeAwsApi
    * Inputs:
        * `DBInstanceReplicaIdentifier`: identifier of the instance, that will be removed
    * Explanation:
        * Adjust size of the cluster by changing a number of nodes removing one Read Replica by
          calling [DeleteDBInstance](https://docs.aws.amazon.com/documentdb/latest/developerguide/API_DeleteDBInstance.html)
1. `VerifyCurrentInstancesCount`
    * Type: aws:executeScript
    * Inputs:
        * `BackupDbClusterInstancesCount.DbClusterInstancesNumber`: initial cluster instances number
        * `DBClusterIdentifier`
   * Outputs:
        * `CurrentInstancesNumber`
    * Explanation:
        * Receives DocDb cluster metadata by API call and counts current instances number. Compares initial and current instances number, current number value must be less then the initial one. API action: [DescribeDBClusters](https://docs.aws.amazon.com/documentdb/latest/developerguide/API_DescribeDBClusters.html)