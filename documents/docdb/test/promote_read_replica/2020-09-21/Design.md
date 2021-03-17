# Id
docdb:test:promote_read_replica:2021-03-16

## Intent
Test DocDb cluster recovering after promoting read replica to primary.

## Type
DocDb failure test

## Risk
Medium

## Requirements
* Available DocumentDB Cluster
* There is a synthetic alarm setup for application
* Application should be able to reconnect to db instance after temporary network errors.

## Permission required for AutomationAssumeRole
* rds:DescribeDBClusters
* rds:FailoverDBCluster
* cloudwatch:DescribeAlarms

## Supports Rollback
No.

## Inputs

### DBClusterIdentifier:
* type: String
* description: (Required) DocDb Cluster Identifier
### DBInstanceReplicaIdentifier:
* type: String
* description: (Required) DocDb Replica Identifier
### SyntheticAlarmName
* Description: (Required) Name of Synthetic alarm for application. This should be green after the test.
* Type: String
### AutomationAssumeRole:
* type: String
* description:
  (Optional) The ARN of the role that allows Automation to perform
  the actions on your behalf. If no role is specified, Systems Manager Automation
  uses your IAM permissions to run this document.
  default: ''

## Document Steps:
1. aws:assertAwsResourceProperty - Assert alarm to be green before test
   * Inputs:
        * SyntheticAlarmName
2. aws:assertAwsResourceProperty - Assert DocDb instances are available
        * Inputs:
            * DBClusterIdentifier
3. aws:executeAutomation - Invoke SOP promote_read_replica
        * Inputs:
            * DocumentName: Digito-PromoteReadReplica_2020-09-21
            * RuntimeParameters:
                * DBClusterIdentifier
                * DBInstanceReplicaIdentifier
                * AutomationAssumeRole
4. aws:waitForAwsResourceProperty - Wait for alarms to be green
        * Inputs:
            * SyntheticAlarmName
