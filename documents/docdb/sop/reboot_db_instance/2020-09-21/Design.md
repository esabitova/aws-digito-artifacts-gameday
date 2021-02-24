# Id
docdb:sop:reboot_db_instance:2020-09-21

## Intent
Used to reboot DB instance when the database doesn’t respond to any requests

## Type
Software Outage SOP

## Risk
Small

## Requirements
* Available DocumentDB Cluster

## Permission required for AutomationAssumeRole
* rds:RebootDBInstance

## Supports Rollback
No.

## Inputs
### DBInstanceIdentifier:
* type: String
* description: (Required) DocDb Instance Identifier
### AutomationAssumeRole:
* type: String
* description: 
    (Optional) The ARN of the role that allows Automation to perform
    the actions on your behalf. If no role is specified, Systems Manager Automation
    uses your IAM permissions to run this document.
    default: ''

## Details of SSM Document steps:
1. `RebootDbInstance`
   * Type: aws:executeAwsApi
   * Inputs:
      * `DBInstanceIdentifier`
   * Explanation:
      * Reboot DB instance when the database doesn’t respond to any requests by
        calling [RebootDBInstance](https://docs.aws.amazon.com/documentdb/latest/developerguide/API_RebootDBInstance.html) 