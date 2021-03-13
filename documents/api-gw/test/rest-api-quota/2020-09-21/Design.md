# Id
api-gw:test:rest-api-quota:2020-09-21

## Intent
Test API Gateway REST API behavior when hitting quota threshold  

## Type
Software Outage Test

## Risk
Medium

## Requirements
* Existing API Gateway REST API
* There is a synthetic alarm setup for application (e.g.api-gw:alarm:5xx-error:2020-04-01, api-gw:alarm:4xx-error:2020-04-01)

## Permission required for AutomationAssumeRole
* TBD

## Supports Rollback
Yes. Users can run the script with `IsRollback` and `PreviousExecutionId` to rollbackup changes from the previous run 

## Input (TBD)
### `AutomationAssumeRole`
  * type: String
  * description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf
### `SyntheticAlarmName`:
  * type: String
  * description: (Required) Alarm which should be green after test
### `AlarmWaitTimeout`
  * type: Integer
  * description: (Optional) Alarm wait timeout
  * default: 300 (seconds)
### `ApiGwId`
  * type: String
  * description: (Required) The ARN of the API Gateway
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
        * `IsRollback` it false, continue with `Backup` step
1. `RollbackPreviousExecution`
    * Type: aws:executeScript
    * Inputs:
        * `PreviousExecutionId`
    * Outputs: 
        * `RestoredValue`: The restored value of Reserved Concurrency.
    * Explanation:
        * Get value of `Backup.Value` from the previous execution using `PreviousExecutionId`
        * https://docs.aws.amazon.com/cli/latest/reference/apigateway/update-usage-plan.html
        * isEnd: true
1. `Backup`
    * Type: aws:executeAwsApi
    * Inputs:
        * `ApiGwId`
    * Outputs:
        * TBD
    * Explanation:
        * https://docs.aws.amazon.com/cli/latest/reference/apigateway/get-usage-plan.html
1. `SetNewValue`
    * Type: aws:executeAwsApi
    * Inputs:
        * `ApiGwId`
    * Outputs: 
        * TBD
    * Explanation:
        * https://docs.aws.amazon.com/cli/latest/reference/apigateway/update-usage-plan.html
    * OnFailure: step: RollbackCurrentChanges 
1. `AssertAlarmToBeRed`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `SyntheticAlarmName`
        * `AlarmWaitTimeout`
    * Outputs: none
    * Explanation:
        * Wait for `SyntheticAlarmName` alarm to be `ALARM` for `AlarmWaitTimeout` seconds
    * OnFailure: step: RollbackCurrentChanges 
1. `RollbackCurrentChanges`
    * Type: aws:executeAwsApi
    * Inputs:
        * `Backup.Value`
    * Outputs:
        * `RestoredValue`
    * Explanation:
        * https://docs.aws.amazon.com/cli/latest/reference/apigateway/update-usage-plan.html
1. `AssertAlarmToBeGreen`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `SyntheticAlarmName`
        * `AlarmWaitTimeout`
    * Outputs: none
    * Explanation:
        * Wait for `SyntheticAlarmName` alarm to be `OK` for `AlarmWaitTimeout` seconds
    * isEnd: true
## Outputs
`Backup.Value`
