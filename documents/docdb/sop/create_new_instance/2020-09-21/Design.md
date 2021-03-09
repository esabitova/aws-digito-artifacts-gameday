# Id
docdb:sop:create_new_instance:2020-09-21

## Intent
Used to create a new instance in a specified AZ/Region

## Type
Create new instance

## Risk
Small

## Requirements
* Available DocumentDB Cluster

## Permission required for AutomationAssumeRole
* rds:CreateDBInstance

## Supports Rollback
No.

## Inputs

### DBInstanceIdentifier
  * Description: (Required) DocDb Instance Identifier
  * Type: String
### DBClusterIdentifier
  * Description: (Required) DocDb Cluster Identifier
  * Type: String
### DBInstanceClass
* Description: (Required) DocDb Instance class
* Type: String
### Engine
* Description: (Required) DocDb Engine
* Type: String
### AvailabilityZone
* Description: (Optional) Availability Zone to place DocDb Instance
* Type: String
### AutomationAssumeRole:
  * Description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf.
  * Type: String

## Details of SSM Document steps:
1. `GetClusterAZ`
   * Type: aws:executeScript
   * Outputs:
      * `CurrentClusterAZ`
   * Inputs:
      * `DBClusterIdentifier`
   * Explanation:
      * Get Availability Zones for DocDb cluster region if Availability Zone is not provided in inputs by
        calling [describe_db_clusters](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/docdb.html#DocDB.Client.describe_db_clusters)
1. `CreateNewInstance`
    * Type: aws:executeScript
    * Inputs:
        * `DBClusterIdentifier`
        * `DBInstanceIdentifier`
        * `DBInstanceClass`
        * `DBClusterAZ`
        * `AvailabilityZone`
        * `Engine`
    * Explanation:
        * Create a new instance in the AZ provided from input or use random AZ for DocDb cluster region by
          calling [create_db_instance](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/docdb.html#DocDB.Client.create_db_instance)
1. `WaitUntilCreatedInstanceAvailable`
   * Type: aws:waitForAwsResourceProperty
   * Inputs:
       * `DBClusterIdentifier`
   * PropertySelector: `$.DBInstances..DBInstanceStatus`
   * Explanation:
       * Wait until created cluster instance become available
