# Id
docdb:test:database_alarm:2020-09-21

## Intent
Test that the alarm setup detects and alerts when database becomes unavailable and Application can recover within expected recovery time

## Type
Test DocDb alarms and outage

## Risk
Medium

## Requirements
* Available DocumentDB Cluster
* There is a synthetic alarm setup for application
* Application should be able to reconnect to db instance after temporary network errors.

## Permission required for AutomationAssumeRole
* rds:DescribeDBClusters
* rds:ModifyDBCluster
* cloudwatch:DescribeAlarms

## Supports Rollback
Yes.

## Inputs
### DBClusterIdentifier:
* type: String
* description: (Required) DocDb Cluster Identifier
### SyntheticAlarmName
* Description: (Required) Name of Synthetic alarm for application. This should be green after the test.
* Type: String
### IsRollback:
  type: String
  description: >-
  (Optional) Set true to 
  default: 'false'
### PreviousExecutionId:
  type: String
  description: >-
  (Optional) Previous execution id for which rollback will be started.
  default: ''
### AutomationAssumeRole:
* type: String
* description: 
    (Optional) The ARN of the role that allows Automation to perform
    the actions on your behalf. If no role is specified, Systems Manager Automation
    uses your IAM permissions to run this document.
    default: ''

## Outputs:
### BackupSGId
### BackupVPCId

## Details of SSM Document steps:
1. aws:branch - Check if the rollback is requested
        * Inputs:
            * IsRollback
        * Explanation:
            * `IsRollback` it true, continue with step 2
            * `IsRollback` it false, continue with step 5
2. aws:executeScript - Prepare rollback, by getting outputs from previous SSM execution
       * Inputs:
            * PreviousExecutionId
       * Outputs:
            * BackupSGId
            * BackupVPCId
            * TempSGId
3. aws:executeScript - Rollback, execute Script to switch to Security group from previous SSM document execution
      * Inputs:
            * step2.BackupSGId
            * step2.BackupVPCId
4. aws:branch - Continue rollback
      * Inputs:
            * IsRollback 
      * Explanation:
            * `IsRollback` it true, continue with step 11
5. aws:assertAwsResourceProperty - Assert alarm to be green before test
        * Inputs:
            * SyntheticAlarmName
6. aws:executeScript - Backup initial Security group Id, VPC Id
        * Inputs:
            * DBClusterIdentifier
        * Outputs:
            * BackupSGId
            * BackupVPCId
7. aws:executeAwsApi - Create temporary Security group
        * Inputs:
            * BackupSGId
            * BackupVPCId
        * Outputs:
            * TempSGId
8. aws:executeScript - execute Script to switch to the temporary Security group
        * Inputs:
            * DBClusterIdentifier
            * TempSecurityGroupId
9. aws:waitForAwsResourceProperty - Wait for alarms to trigger
        * Inputs:
            * SyntheticAlarmName
10. aws:executeScript - execute Script to switch to the initial Security group
        * Inputs:
            * DBClusterIdentifier
            * BackupSGId
11. aws:executeScript - Remove temporary Security group and verify if it exists during the rollback
        * Inputs:
            * TempSGId
12. aws:waitForAwsResourceProperty - Wait for alarms to be green
        * Inputs:
            * SyntheticAlarmName
