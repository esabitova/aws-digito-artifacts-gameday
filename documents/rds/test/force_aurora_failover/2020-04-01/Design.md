# https://github.com/aws-samples/aws-digito-artifacts-spec/blob/master/components/databases/rds/rds-gameday.adoc#test---force-aurora-failover

# Id
rds:test:force_aurora_failover:2020/04/01

## Intent
Test that the application automatically recovers in case of an automatic aurora in-region failover

## Type
AZ Failure Test

## Risk
Medium

## Requirements
* Database AppComponent with an aurora cluster with a writer and a read replica in same region.
* There is a synthetic alarm setup for application
* Application should be able to reconnect to db instance after temporary network errors.

## Permission required for AutomationAssumeRole
* rds.describe_db_clusters
* rds.failover_db_cluster
* cloudwatch.describe_alarms

## Supports Rollback
No.

## Inputs
### DbClusterId
  * Description: (Required) Identifies the db cluster that will be failed over.
  * Type: String
### DbInstanceId
  * Description: (Optional) Identifies the db instance that will be promoted to primary.
  * Type: String
  * Default: Selects default db instance to promote
### SyntheticAlarmName
  * Description: (Required) Name of Synthetic alarm for application. This should be green after the test.
  * Type: String
### AutomationAssumeRole:
  * Description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf. See Permissions required above for test.
  * Type: String

## Details
  * Failover Aurora DB Cluster.
  * Wait for cluster to be available.
  * Verify that Synthetic monitor turns green within x minutes.

## Outputs
The automation execution has no outputs
