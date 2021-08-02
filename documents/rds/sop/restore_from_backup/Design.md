# Id
rds:sop:restore_from_backup:2020-04-01

## Intent
SOP from Digito to restore a single AZ RDS DB from backup

## Type
SOFTWARE

## Risk
MEDIUM

## Requirements
* a single AZ RDS DB with backup

## Permission required for AutomationAssumeRole
* rds:DeleteDBInstance
* rds:DescribeDBInstances
* rds:DescribeDBSnapshots
* rds:ModifyDBInstance
* rds:RestoreDBInstanceFromDBSnapshot

## Supports Rollback
Yes.

## Inputs

### DbInstanceIdentifier
  * Description: (Required) The identifier of the source DB instance with at least one read replica
  * Type: String
### Dryrun
  * Description: (Optional) Dryrun indicates a testing run, changes will be rolled back.
  * Type: String
### AutomationAssumeRole:
  * Description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf.
  * Type: String
  
## Outputs
  * `OutputRecoveryTime.RecoveryTime`: recovery time in seconds

## Details of SSM Document steps:
See SOP implementation (the Design.md was written after the actual implementation)