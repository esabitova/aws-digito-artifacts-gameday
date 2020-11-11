# Not present in spec, Test for https://code.amazon.com/packages/AwsDigitoAssessmentExecutor/blobs/mainline/--/src/com/amazonaws/digito/assessmentservice/executor/recommender/sop/rds/RdsRestoreToPointInTimeSop.java

# Id
rds:test:restore_to_pit_sop:20/04/01

## Intent
Test that the application automatically recovers after point in time restore

## Type
SOP Test

## Risk
Medium

## Requirements
* RDS database with backup and point in time restore enabled
* There is a synthetic alarm setup for application
* Application should be able to reconnect to db instance after temporary network errors.

## Permission required for AutomationAssumeRole
* rds.describe_db_instances
* rds.delete_db_instance
* cloudwatch.describe_alarms
* ssm.get_automation_execution

## Supports Rollback
No.

## Inputs

### DbInstanceIdentifier
  * Description: (Required) Identifies the db instance subject to action.
  * Type: String
### SyntheticAlarmName
  * Description: (Required) Name of Synthetic alarm for application. This should be green after the test.
  * Type: String
### AutomationAssumeRole:
  * Description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf. See Permissions required above for test.
  * Type: String

## Details
  * Restore rds database to point in time
  * Wait for new instance to come back up.
  * Rename old instance to temp
  * Rename new instance to same as original identifier
  * Verify that Synthetic monitor turns red within x minutes.
  * Verify that Synthetic monitor turns green within x minutes.
  * Delete old instance

## Outputs
The automation execution has no outputs
