# Id
api-gw:test:rest-api-quota:2020-09-21

## Intent
Test API Gateway REST API behavior when hitting quota threshold  

## Type
Software Outage Test

## Risk
HIGH

## Requirements
* Existing API Gateway REST API
* There is a synthetic alarm setup for application (e.g.api-gw:alarm:5xx-error:2020-04-01, api-gw:alarm:4xx-error:2020-04-01)

## Permission required for AutomationAssumeRole
* apigateway:GET
* apigateway:PATCH
* cloudwatch:DescribeAlarms
* ssm:GetAutomationExecution
* ssm:StartAutomationExecution
* ssm:GetParameters
* iam:PassRole

## Supports Rollback
Yes. Users can run the script with `IsRollback` and `PreviousExecutionId` to rollback changes from the previous run 

## Input
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
### `RestApiGwUsagePlanId`
  * type: String
  * description: (Required) The ID of REST API Gateway usage plan
### `IsRollback`:
  * type: Boolean
  * description: (Optional) Run rollback step of the given previous execution (parameter `PreviousExecutionId`)
  * default: False
### `PreviousExecutionId`:
  * type: Integer
  * description: (Optional) The id of previous execution of the current script
  * default: 0
### `RestApiGwQuotaLimit`:
  * type: Integer
  * description: (Optional) The value of quota (requests per period).
  * default: 1
### `RestApiGwQuotaPeriod`:
  * type: String
  * description: (Optional) The value of quota period. Possible values: DAY, WEEK, MONTH. 
  * default: DAY

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
        * `RestApiGwQuotaLimitRestoredValue` returns `rateLimit`
        * `RestApiGwQuotaPeriodRestoredValue` returns `burstLimit`
    * Explanation:
        * Get values from the previous execution using `PreviousExecutionId`, take values
          of `BackupQuotaConfigurationAndInputs` step
            * `quota`=`BackupQuotaConfigurationAndInputs.RestApiGwQuotaLimitOriginalValue`
            * `quotaPeriod`=`BackupQuotaConfigurationAndInputs.RestApiGwQuotaPeriodOriginalValue`
            * `usagePlanId`=`BackupQuotaConfigurationAndInputs.RestApiGwUsagePlanId`
        *
        Execute https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/apigateway.html#APIGateway.Client.update_usage_plan
        with the following parameters:
            * `usagePlanId`= `RestApiGwUsagePlanId`
            * `patchOperations`
              =`op="replace",path="/quota/limit",value="<quota>",op="replace",path="/quota/period",value="<quotaPeriod>"`
            * Use `quota` sections in the root of the response and return `limit` and `period`
        * isEnd: true
1. `BackupQuotaConfigurationAndInputs`
    * Type: aws:executeScript
    * Inputs:
        * `RestApiGwUsagePlanId`
    * Outputs:
        * `RestApiGwUsagePlanId`
        * `RestApiGwQuotaLimitOriginalValue` returns `limit`
        * `RestApiGwQuotaPeriodOriginalValue` returns `period`
    * Explanation:
        * Execute https://docs.aws.amazon.com/cli/latest/reference/apigateway/get-usage-plan.html
            * Use `quota` sections in the root or the response and return `limit` and `period`
1. `SetQuotaConfiguration`
    * Type: aws:executeScript
    * Inputs:
        * `RestApiGwUsagePlanId`
        * `RestApiGwQuotaLimit`
        * `RestApiGwQuotaPeriod`
    * Outputs: 
        * `RestApiGwQuotaLimitNewValue` returns `limit`
        * `RestApiGwQuotaPeriodNewValue` returns `period`
    * Explanation:
        * Define variables
            * `quota`=`RestApiGwQuotaLimit`
            * `quotaPeriod`=`RestApiGwQuotaPeriod`
            * `usagePlanId`=`RestApiGwUsagePlanId`
        * Execute https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/apigateway.html#APIGateway.Client.update_usage_plan with the following parameters:
            * `usagePlanId`= `RestApiGwUsagePlanId`
            * `patchOperations`=`op="replace",path="/quota/limit",value="<quota>",op="replace",path="/quota/period",value="<quotaPeriod>"`
            * Use `quota` sections in the root of the response and return `limit` and `period`
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
    * Type: aws:executeScript
    * Inputs: none
    * Outputs:
        * `RestApiGwQuotaLimitRestoredValue` returns `rateLimit`
        * `RestApiGwQuotaPeriodRestoredValue` returns `burstLimit`
    * Explanation:
        * Define variables using outputs of `BackupQuotaConfigurationAndInputs`:
            * `quota`=`BackupQuotaConfigurationAndInputs.RestApiGwQuotaLimitOriginalValue`
            * `burstLimit`=`BackupQuotaConfigurationAndInputs.RestApiGwQuotaPeriodOriginalValue`
            * `usagePlanId`=`BackupQuotaConfigurationAndInputs.RestApiGwUsagePlanId`
        *
        Execute https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/apigateway.html#APIGateway.Client.update_usage_plan
        with the following parameters:
            * `usagePlanId`= `RestApiGwUsagePlanId`
            * `patchOperations`
              =`op="replace",path="/quota/limit",value="<quota>",op="replace",path="/quota/period",value="<quotaPeriod>"`
            * Use `quota` sections in the root of the response and return `limit` and `period`
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
* `BackupQuotaConfigurationAndInputs.RestApiGwUsagePlanId`
* `BackupQuotaConfigurationAndInputs.RestApiGwQuotaLimitOriginalValue` - original value of quota limit
* `BackupQuotaConfigurationAndInputs.RestApiGwQuotaPeriodOriginalValue` - original value of quota period


if `IsRollback`:
* `RollbackPreviousExecution.RestApiGwQuotaLimitRestoredValue`
* `RollbackPreviousExecution.RestApiGwQuotaPeriodRestoredValue`

if not `IsRollback`:
* `SetQuotaConfiguration.RestApiGwQuotaLimitNewValue` - new value of quota limit
* `SetQuotaConfiguration.RestApiGwQuotaPeriodNewValue` - new value of quota period