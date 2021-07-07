# Id
rds:sop:promote_non_aurora_replica:2020-04-01

## Intent
SOP from Digito to recover an instance by promoting a replica to master in case of failure in the master instance

## Type
HARDWARE

## Risk
MEDIUM

## Requirements
* RDS db with at least one read replica

## Permission required for AutomationAssumeRole
* rds:CreateDBInstanceReadReplica
* rds:DeleteDBInstance
* rds:DescribeDBInstances
* rds:ModifyDBInstance
* rds:PromoteReadReplica

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