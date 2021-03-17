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
### TempSecurityGroupId
* Description: (Required) Id of the temporary security group. This should used during the switching.
* Type: String
### AutomationAssumeRole:
* type: String
* description: 
    (Optional) The ARN of the role that allows Automation to perform
    the actions on your behalf. If no role is specified, Systems Manager Automation
    uses your IAM permissions to run this document.
    default: ''

## Details of SSM Document steps:
1. aws:assertAwsResourceProperty - Assert alarm to be green before test
        * Inputs:
            * SyntheticAlarmName
2. aws:executeScript - execute Script to switch to the temporary Security group
        * Inputs:
            * DBClusterIdentifier
            * TempSecurityGroupId
3. aws:waitForAwsResourceProperty - Wait for alarms to trigger
        * Inputs:
            * SyntheticAlarmName
4. aws:executeScript - execute Script to switch to the initial Security group
        * Inputs:
            * DBClusterIdentifier
            * TempSecurityGroupId
3. aws:waitForAwsResourceProperty - Wait for alarms to be green
        * Inputs:
            * SyntheticAlarmName
