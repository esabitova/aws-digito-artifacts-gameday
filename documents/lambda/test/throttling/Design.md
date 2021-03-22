# Id
lambda:test:throttling:2020-09-21

## Intent
Test Lambda behavior when hitting ReservedConcurrentExecutions value 

## Type
Software Outage Test

## Risk
Medium

## Requirements
* Existing Lambda Function
* There is a synthetic alarm setup for application

## Permission required for AutomationAssumeRole
* lambda:PutFunctionConcurrency
* lambda:GetFunctionConcurrency
* lambda:InvokeFunction
* cloudwatch:DescribeAlarms

## Supports Rollback
Yes. The script backups existing Reserved Concurrency value and restores it when the specified alarms fires.
Users can run the script with `IsRollback` and `PreviousExecutionId` to rollback changes from the previous run 

## Inputs
### `AutomationAssumeRole`
  * type: String
  * description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf
### `SyntheticAlarmName`:
  * type: String
  * description: (Required) Alarm which should be green after test
### `LambdaARN`
  * type: String
  * description: (Required) The ARN of the Lambda function
### `NewReservedConcurrentExecutions`:
  * type: Integer
  * description: (Required) New reserved concurrent executions
  * default: 0
### `IsRollback`:
  * type: Boolean
  * description: (Optional) Run rollback step of the given previous execution (parameter `PreviousExecutionId`)
  * default: False
### `PreviousExecutionId`:
  * type: Integer
  * description: (Optional) The id of previous execution of the current script
  * default: 0

## Details of SSM Document steps:
1. `CheckIsRollback`
    * Type: aws:branch
    * Inputs:
        * `IsRollback`
    * Outputs: none
    * Explanation:
        * `IsRollback` it true, continue with `RollbackPreviousExecution` step
        * `IsRollback` it false, continue with `BackupReservedConcurrentExecutions` step
1. `RollbackPreviousExecution`
    * Type: aws:executeScript
    * Inputs:
        * `PreviousExecutionId`
    * Outputs: 
        * `RestoredReservedConcurrentExecutionsValue`: The restored value of Reserved Concurrency.
    * Explanation:
        * Get values from previous execution by `PreviousExecutionId`
          * `previousLambdaArn` = `BackupReservedConcurrentExecutions.LambdaARN` 
          * `previousConcurrentExecutionsValue` = `BackupReservedConcurrentExecutions.BackupReservedConcurrentExecutionsValue` 
        * Check if `previousLambdaArn` equals to `LambdaARN` if not raise an error
        * Set `BackupReservedConcurrentExecutions.BackupReservedConcurrentExecutionsValue` using  [put_function_concurrency](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/lambda.html#Lambda.Client.put_function_concurrency). Parameters:
          * `FunctionName`='`LambdaARN`',
          * `ReservedConcurrentExecutions`=`previousConcurrentExecutionsValue`
        * Return `ReservedConcurrentExecutions` API JSON response
        * isEnd: true
1. `BackupReservedConcurrentExecutions`
    * Type: aws:executeAwsApi
    * Inputs:
        * `LambdaARN`
    * Outputs:
        * `BackupReservedConcurrentExecutionsValue`
        * `LambdaARN` - returns inputs
    * Explanation:
        * Get Function concurrency using [get_function_concurrency](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/lambda.html#Lambda.Client.get_function_concurrency)
            * Parameters:
                * FunctionName='`LambdaARN`'
            * Return `.ReservedConcurrentExecutions`
1. `UpdateReservedConcurrentExecutions`
    * Type: aws:executeAwsApi
    * Inputs:
        * `LambdaARN`
    * Outputs: 
        * `ReservedConcurrentExecutionsNewValue`
    * Explanation:
        * Set `0` using  [put_function_concurrency](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/lambda.html#Lambda.Client.put_function_concurrency). Parameters:
          * `FunctionName`='`LambdaARN`',
          * `ReservedConcurrentExecutions`=`0`
        * Return `ReservedConcurrentExecutions` API JSON response
    * OnFailure: step: RollbackToPreviousReservedConcurrentExecutions 
1. `AssertAlarmToBeRed`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `SyntheticAlarmName`
    * Outputs: none
    * Explanation:
        * Wait for `SyntheticAlarmName` alarm to be `ALARM` for `600` seconds
    * OnFailure: step: RollbackToPreviousReservedConcurrentExecutions 
1. `RollbackToPreviousReservedConcurrentExecutions`
    * Type: aws:executeAwsApi
    * Inputs:
        * `BackupReservedConcurrentExecutions.BackupReservedConcurrentExecutionsValue`
    * Outputs:
        * `ReservedConcurrentExecutionsRestoredValue`: The restored value of Reserved Concurrency.
    * Explanation:
        * Set `BackupReservedConcurrentExecutions.BackupReservedConcurrentExecutionsValue` using  [put_function_concurrency](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/lambda.html#Lambda.Client.put_function_concurrency). Parameters:
          * FunctionName='`LambdaARN`',
          * ReservedConcurrentExecutions=`BackupReservedConcurrentExecutions.BackupReservedConcurrentExecutionsValue`
        * Return `ReservedConcurrentExecutions` API JSON response
1. `AssertAlarmToBeGreen`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `SyntheticAlarmName`
    * Outputs: none
    * Explanation:
        * Wait for `SyntheticAlarmName` alarm to be `OK` for `600` seconds
    * isEnd: true
## Outputs
* `BackupReservedConcurrentExecutions.BackupReservedConcurrentExecutionsValue`
* `BackupReservedConcurrentExecutions.LambdaARN`

if `IsRollback`:
* `RollbackPreviousExecution.RestoredReservedConcurrentExecutionsValue`

if not `IsRollback`:
* `UpdateReservedConcurrentExecutions.ReservedConcurrentExecutionsNewValue`
* `RollbackToPreviousReservedConcurrentExecutions.ReservedConcurrentExecutionsRestoredValue`