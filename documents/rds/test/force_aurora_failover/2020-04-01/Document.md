# Id
rds:test:force_aurora_failover:2020-04-01

## Document Type
Automation

## Description
Test that the application automatically recovers in case of an automatic aurora in-region failover

## Disruption Type
AZ

## Risk
SMALL

## Permissions required
    * rds:DescribeDBClusters
    * rds:FailoverDBCluster
    * cloudwatch:DescribeAlarms

## Depends On
None

## Supports Rollback
No

## Recommended Alarms
None

## Inputs
### `ClusterId`
    * type: String
    * description: (Required) Identifies the Aurora cluster subject to action.
### `InstanceId`
    * type: String
    * description: (Optional) The DB instance to promote to the primary instance.
### `SyntheticAlarmName`
    * type: String
    * description: (Required) Alarm which should be green after test.
### `AutomationAssumeRole`
    * type: String
    * description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf.

## Outputs
None
