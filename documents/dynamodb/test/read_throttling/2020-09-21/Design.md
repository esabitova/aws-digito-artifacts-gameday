# Id
dynamodb:test:read_throttling:2020-09-21

## Intent
Test that the ReadThrottleEvents metric alarm setup detects and alerts when table becomes unavailable

## Type
HW Instance Failure Test 

## Risk
Small

## Requirements
* A DynamoDB Table if it is not on-demand or provisioned capacity with the autoscaling enabled
* The DynamoDB Table should be actively read during the last minutes before the execution to get right average values of `ConsumedReadCapacityUnits` metric
* An alarm setup for ReadThrottleEvents metric

## Permission required for AutomationAssumeRole
* dynamodb:DescribeTable
* dynamodb:UpdateTable
* cloudwatch:DescribeAlarms

## Supports Rollback
Yes.

* Explanation: The rollback backups existing dynamodb table RCU as well as WCU values (they can not be updated separately by API method) and restores it when the specified alarms fires. Users can run the script with IsRollback and PreviousExecutionId to rollbackup changes from the previous run

## Inputs

### DynamoDBTableName

* Description: (Required) The DynamoDB Table Name.
* Type: String

### ReadThrottleAlarmName

* Description: (Required) Alarm which should be green after test.
* Type: String

### AlarmWaitTimeout

* Description: (Optional) Alarm wait timeout
* Type: Integer
* Default: 300 (seconds)

### MetricDurationMinutes

* Description: (Optional) The duration in minutes which will be used to get average value of ConsumedReadCapacityUnits metric of the specified DynamoDB table. Not less than 1 minute.
* Type: Integer
* Default: 10 (minutes)

### AutomationAssumeRole

* Description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf. See Permissions required above for test.
* Type: String

### IsRollback:

* type: String
* description: (Optional) Provide true to cleanup appliance created in previous execution. Can be either true or false.
* default: 'false'

### PreviousExecutionId:

* type: String
* description: (Optional) Previous execution id for which resources need to be cleaned up.
* default: ''

## Details of SSM Document steps:

1. `CheckIsRollback`
    * Type: aws:branch
    * Inputs:
        * `IsRollback`
    * Outputs: none
    * Explanation:
        * If `IsRollback` is true, go to the step `RollbackPreviousExecution`.
        * If `IsRollback` is false, proceed to the step `ValidateMetricDurationMinutes`

1. `RollbackPreviousExecution`:
    * Type: aws:executeScript
    * Inputs:
        * `PreviousExecutionId`: The id of the previous execution which has to be rolled back to the initial state.
    * Outputs:
        * `RestoredReadCapacityUnits`: The restored value of the dynamodb table RCU
    * Explanation:
        * Get values of `BackupDynamodbTableProvisionedThroughput.BackupReadCapacityUnits` and `BackupDynamodbTableProvisionedThroughput.BackupWriteCapacityUnits`  from the previous execution
          using `PreviousExecutionId`
        * Call [update_table](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_UpdateTable.html) method to update the dynamodb table RCU by passing the `DynamoDBTableName` and
          the `ProvisionedThroughput` `BackupDynamodbTableProvisionedThroughput.BackupReadCapacityUnits` and `BackupDynamodbTableProvisionedThroughput.BackupWriteCapacityUnits` properties as the
          arguments.
    * isEnd: true

1. `ValidateMetricDurationMinutes`
    * Type: aws:branch
    * Inputs:
       * `MetricDurationMinutes`
    * Outputs: none
    * Explanation:
        * If `MetricDurationMinutes` is less than 1, fail here.
        * Otherwise, go further to `BackupDynamodbTableProvisionedThroughput`


1. `BackupDynamodbTableProvisionedThroughput`
    * Type: aws:executeAwsApi
    * Inputs:
        * `Service`: dynamodb
        * `Api`: DescribeTable
        * `TableName`: pass DynamoDBTableName parameter
    * Outputs:
        * `BackupReadCapacityUnits`: The dynamoDB table `ReadCapacityUnits` value from the `ProvisionedThroughput` property
        * `BackupWriteCapacityUnits`: The dynamoDB table `WriteCapacityUnits` value from the `ProvisionedThroughput` property
    * Explanation:
        * Get the source dynamodb table stream properties as they are not restored by the
          backup. `[describe_table](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_DescribeTable.html)
          method

1. `CalculateStartAndEndTimes`
    * Type: aws:executeScript
    * Inputs:
        * `MetricDurationMinutes`: integer value of minutes, must be rounded not to be float
    * Outputs:
        * `StartTime`: now()-`MetricDurationMinutes` minute(-s) in Timestamp
        * `EndTime`: now() in Timestamp

1. `GetConsumedReadCapacityUnits`
    * Type: aws:executeAwsApi
    * Inputs:
       * `Service`: cloudwatch
       * `Api`: GetMetricStatistics
       * `MetricName`: ConsumedReadCapacityUnits
        * `StartTime`: `CalculateStartAndEndTimes.StartTime`
        * `EndTime`: `CalculateStartAndEndTimes.EndTime`
        * `Period`: `MetricDurationMinutes`
        * `Statiscis`: Average
    * Outputs:
        * `ConsumedReadCapacityUnits`

1. `GetLowerConsumedReadCapacityUnits`
    * Type: aws:executeScript
    * Inputs:
        * `Value`: `GetConsumedReadCapacityUnits.ConsumedReadCapacityUnits`
        * `MathExpression`: "Value-Value*0.1"
    * Outputs:
        * `Result`: lower than original `ConsumedReadCapacityUnits` metric
    * Explanation:
        * Apply `MathExpression` by Python's eval() function where the input will be updated by replacing Value with `Value` and `MathExpression` will be validated to have only allowed safe chars 0123456789+-*()./ 

1. `UpdateDynamodbTableRCU`
    * Type: aws:executeAwsApi
    * Inputs:
       * `Service`: dynamodb
       * `Api`: UpdateTable
       * `TableName`: pass DynamoDBTableName parameter
       * `ProvisionedThroughput`: pass `GetLowerConsumedReadCapacityUnits.Result` for `ReadCapacityUnits` and the `BackupWriteCapacityUnits` value for `WriteCapacityUnits` from the previous step
    * Outputs:
       * `UpdatedReadCapacityUnits`: The dynamoDB table updated `ReadCapacityUnits` value from the `ProvisionedThroughput` property
       * `UpdatedWriteCapacityUnits`: The dynamoDB table updated `WriteCapacityUnits` value from the `ProvisionedThroughput` property
    * Explanation:
       * Change the dynamodb table `ReadCapacityUnits` provisioned throughput property. [update_table](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_UpdateTable.html) method
    * OnFailure: go to step `RollbackCurrentExecution`

1. `VerifyDynamoDBTableStatusAfterUpdateDynamodbTableRCU`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `Service`: dynamodb
        * `Api`: DescribeTable
        * `TableName`: pass DynamoDBTableName parameter
        * `PropertySelector`: use the $.Table.TableStatus selector
            * `DesiredValues`: needs to be in ACTIVE status
    * Explanation:
      * Wait for the table to be in ACTIVE status. [describe_table](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_DescribeTable.html) method
   * OnFailure: go to step `RollbackCurrentExecution`

1. `AssertAlarmToBeRed`
   * Type: aws:waitForAwsResourceProperty
   * TimeoutSeconds: pass AlarmWaitTimeout parameter
   * Inputs:
      * `Service`: cloudwatch
        * `Api`: DescribeAlarms
        * `AlarmNames`: pass ReadThrottleAlarmName parameter in a list
    * Outputs: none
    * Explanation:
        * Wait for `ReadThrottleAlarmName` alarm to be ALARM for `AlarmWaitTimeout` seconds. [describe_alarms](https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/API_DescribeAlarms.html) method
    * OnFailure: go to step `RollbackCurrentExecution`

1. `RollbackCurrentExecution` 
    * Type: aws:executeAwsApi
    * Inputs:
        * `Service`: dynamodb
        * `Api`: UpdateTable
        * `TableName`: pass DynamoDBTableName parameter
        * `ProvisionedThroughput`: pass the `BackupReadCapacityUnits` value for `ReadCapacityUnits` and the `BackupWriteCapacityUnits` value for `WriteCapacityUnits` from the `BackupDynamodbTableProvisionedThroughput` step
    * Outputs:
        * `ActualReadCapacityUnits`: The dynamoDB table actual `ReadCapacityUnits` value from the `ProvisionedThroughput` property
        * `ActualWriteCapacityUnits`: The dynamoDB table actual `WriteCapacityUnits` value from the `ProvisionedThroughput` property
    * Explanation:
        * Rollback to the dynamodb table previous `ReadCapacityUnits` provisioned throughput property. `[update_table](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_UpdateTable.html) method

1. `VerifyDynamoDBTableStatusAfterRollbackToPreviousDynamoDBTableRCU`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `Service`: dynamodb
        * `Api`: DescribeTable
        * `TableName`: pass DynamoDBTableName parameter
        * `PropertySelector`: use the $.Table.TableStatus selector
        * `DesiredValues`: needs to be in ACTIVE status 
    * Explanation:
        * Wait for the table to be in ACTIVE status. [describe_table](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_DescribeTable.html) method

1. `AssertAlarmToBeGreen`
    * Type: aws:waitForAwsResourceProperty
    * TimeoutSeconds: pass AlarmWaitTimeout parameter
    * Inputs:
        * `Service`: cloudwatch
        * `Api`: DescribeAlarms
        * `AlarmNames`: pass ReadThrottleAlarmName parameter in a list
    * Outputs: none
    * Explanation:
        * Wait for `ReadThrottleAlarmName` alarm to be OK for `AlarmWaitTimeout` seconds. [describe_alarms](https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/API_DescribeAlarms.html) method
    * isEnd: true

## Outputs
No.