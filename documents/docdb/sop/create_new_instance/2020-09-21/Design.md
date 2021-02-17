# Id
docdb:sop:create_new_instance:2020-09-21

## Intent
Used to create a new instance in a specified AZ/Region when a database can’t be restored from Point-In-Time backup

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
* Description: (Required) DocDb instance Availability Zone
* Type: String
### AutomationAssumeRole:
  * Description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf.
  * Type: String

## Details of SSM Document steps:
1. `CreateNewInstance`
    * Type: aws:executeAwsApi
    * Inputs:
        * `DBInstanceIdentifier`
        * `DBInstanceClass`
        * `DBClusterIdentifier`
        * `Engine`
        * `AvailabilityZone`
    * Explanation:
        * Used to create a new instance by
          calling [CreateDBInstance](https://docs.aws.amazon.com/documentdb/latest/developerguide/API_CreateDBInstance.html) 
