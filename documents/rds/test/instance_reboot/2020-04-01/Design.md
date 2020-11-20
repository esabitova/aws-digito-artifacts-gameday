# https://github.com/aws-samples/aws-digito-artifacts-spec/blob/master/components/databases/rds/rds-gameday.adoc#test---recover-from-rds-reboot

# Id
rds:test:instance_reboot:2020-04-01

## Intent
Test that the application automatically recovers in case of an automatic MAZ failover

## Type
HW Instance Failure Test

## Risk
Small

## Requirements
* RDS database
* There is a synthetic alarm setup for application
* Application should be able to reconnect to db instance after temporary network errors.

## Permission required for AutomationAssumeRole
* rds.describe_db_instances
* rds.reboot_db_instance
* cloudwatch.describe_alarms

## Supports Rollback
No.

## Inputs

### DbInstanceId
  * Description: (Required) Identifies the db instance subject to action.
  * Type: String
### SyntheticAlarmName
  * Description: (Required) Name of Synthetic alarm for application. This should be green after the test.
  * Type: String
### AutomationAssumeRole:
  * Description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf. See Permissions required above for test.
  * Type: String

## Details
  * Reboot db instance
  * Wait for instance to come back up.
  * Verify that Synthetic monitor turns green within x minutes.

## Outputs
The automation execution has no outputs
