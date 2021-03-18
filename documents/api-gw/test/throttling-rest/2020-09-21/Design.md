# Id
api-gw:test:throttling-rest:2020-09-21

## Intent
Test API Gateway REST API behavior when hitting throttling threshold  

## Type
Software Outage Test

## Risk
High

## Requirements
* Existing API Gateway REST API
* There is a synthetic alarm setup for application (e.g.api-gw:alarm:5xx-error:2020-04-01, api-gw:alarm:4xx-error:2020-04-01)

## Permission required for AutomationAssumeRole
* apigateway:GET
* apigateway:PUT

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
### `RestApiId`
  * type: String
  * description: (Required) The ID of REST API Gateway
### `RestApiGwStageName`
  * type: String
  * description: (Optional) The name of the Stage which throttling settings should be applied to. If not set, setting will be applied on the Usage Plan level. 
### `RestApiGwResourcePath`
  * type: String
  * description: (Optional) The Resource Path which throttling settings should be applied to (e.g. /Customers/Accounts/). Can be set as "*" (all resources). if `RestApiGwStageName` is not provided then this parameter is ignored
  * default: "*"
### `RestApiGwHttpMethod`
  * type: String
  * description: (Optional) The HTTP method which throttling settings should be applied to (e.g. GET, POST, PUT, and etc.). Can be set as "*" (all http methods). if `RestApiGwStageName` is not provided then this parameter is ignored
  * default: "*"
### `IsRollback`:
  * type: Boolean
  * description: (Optional) Run rollback step of the given previous execution (parameter `PreviousExecutionId`)
  * default: False
### `PreviousExecutionId`:
  * type: Integer
  * description: (Optional) The id of previous execution of the current script
  * default: 0
### `RestApiGwThrottlingRate`:
  * type: Integer
  * description: (Optional) The value of throttling rate (requests per second)
  * default: 0
### `RestApiGwThrottlingBurst`:
  * type: Integer
  * description: (Optional) The value of throttling rate (requests)
  * default: 0

## Details of SSM Document steps:
1. `CheckIsRollback`
    * Type: aws:branch
    * Inputs:
        * `IsRollback`
    * Outputs: none
    * Explanation:
        * `IsRollback` it true, continue with `RollbackPreviousExecution` step
        * `IsRollback` it false, continue with `BackupThrottlingConfigurationAndInputs` step
1. `RollbackPreviousExecution`
    * Type: aws:executeScript
    * Inputs:
        * `PreviousExecutionId`
    * Outputs: 
        * `RestApiGwThrottlingRateRestoredValue` returns `rateLimit`
        * `RestApiGwThrottlingBurstRestoredValue` returns `burstLimit`
    * Explanation:
        * Get values from the previous execution using `PreviousExecutionId`, take values of `BackupThrottlingConfigurationAndInputs` step
            * `rateLimit`=`BackupThrottlingConfigurationAndInputs.RestApiGwThrottlingRateOriginalValue`
            * `burstLimit`=`BackupThrottlingConfigurationAndInputs.RestApiGwThrottlingBurstOriginalValue`
            * `usagePlanId`=`BackupThrottlingConfigurationAndInputs.RestApiGwUsagePlanId`
            * `apidId`=`BackupThrottlingConfigurationAndInputs.RestApiId`
            * `stageName`=`BackupThrottlingConfigurationAndInputs.RestApiGwStageName`
            * `resourcePath`=`BackupThrottlingConfigurationAndInputs.RestApiGwResourcePath`, if empty use "*"
            * `httpMethod`=`BackupThrottlingConfigurationAndInputs.RestApiGwHttpMethod`, it empty use "*"
        * if `stageName` is not null
            * Execute https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/apigateway.html#APIGateway.Client.update_usage_plan with the following parameters:
                * `usagePlanId`= `RestApiGwUsagePlanId`
                * `patchOperations`=`op="replace",path="/apiStages/<apidId:stageName>/throttle/<resourcePath>/<httpMethod>/rateLimit",value="<rateLimit>",op="replace",path="/apiStages/<apidId:stageName>/throttle/<resourcePath>/<httpMethod>/burstLimit",value="<burstLimit>"`
                * Filter out `apiStages` section of the response according to provided `RestApiId`, `RestApiGwStageName`, `RestApiGwResourcePath`, `RestApiGwHttpMethod` values and return `burstLimit` and `rateLimit` from `throttle` section
        * if `stageName` is null
            * Execute https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/apigateway.html#APIGateway.Client.update_usage_plan with the following parameters:
                * `usagePlanId`= `RestApiGwUsagePlanId`
                * `patchOperations`=`op="replace",path="/throttle/rateLimit",value="<rateLimit>",op="replace",path="/throttle/burstLimit",value="<burstLimit>"`
                * Use `throttle` sections in the root of the response and return `burstLimit` and `rateLimit`
        * isEnd: true
1. `BackupThrottlingConfigurationAndInputs`
    * Type: aws:executeScript
    * Inputs:
        * `RestApiGwUsagePlanId`
        * `RestApiId`
        * `RestApiGwStageName`
        * `RestApiGwResourcePath`
        * `RestApiGwHttpMethod`
    * Outputs:
        * `RestApiGwUsagePlanId`
        * `RestApiId`
        * `RestApiGwStageName`
        * `RestApiGwResourcePath`
        * `RestApiGwHttpMethod`
        * `RestApiGwThrottlingRateOriginalValue` returns `rateLimit`
        * `RestApiGwThrottlingBurstOriginalValue` returns `burstLimit`
    * Explanation:
        * Execute https://docs.aws.amazon.com/cli/latest/reference/apigateway/get-usage-plan.html
            * if `RestApiGwStageName` is not null:
                * Filter out `apiStages` section of the response according to provided `RestApiId`, `RestApiGwStageName`, `RestApiGwResourcePath`, `RestApiGwHttpMethod` values and return `burstLimit` and `rateLimit` from `throttle` section
            * if `RestApiGwStageName` is null:
                * Use `throttle` sections in the root or the response and return `burstLimit` and `rateLimit`
1. `SetThrottlingConfiguration`
    * Type: aws:executeScript
    * Inputs:
        * `RestApiGwUsagePlanId`
        * `RestApiId`
        * `RestApiGwStageName`
        * `RestApiGwResourcePath`
        * `RestApiGwHttpMethod`
        * `RestApiGwThrottlingRate`
        * `RestApiGwThrottlingBurst`
    * Outputs: 
        * `RestApiGwThrottlingRateNewValue` returns `rateLimit`
        * `RestApiGwThrottlingBurstNewValue` returns `burstLimit`
    * Explanation:
        * Define variables
            * `newRateLimit`=`RestApiGwThrottlingRate`
            * `newBurstLimit`=`RestApiGwThrottlingBurst`
            * `usagePlanId`=`RestApiGwUsagePlanId`
            * `apidId`=`RestApiId`
            * `stageName`=`RestApiGwStageName`
            * `resourcePath`=`RestApiGwResourcePath`, if empty use "*"
            * `httpMethod`=`RestApiGwHttpMethod`, it empty use "*"
        * if `stageName` is not null
            * Execute https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/apigateway.html#APIGateway.Client.update_usage_plan with the following parameters:
                * `usagePlanId`= `RestApiGwUsagePlanId`
                * `patchOperations`=`op="replace",path="/apiStages/<apidId:stageName>/throttle/<resourcePath>/<httpMethod>/rateLimit",value="<newRateLimit>",op="replace",path="/apiStages/<apidId:stageName>/throttle/<resourcePath>/<httpMethod>/burstLimit",value="<newBurstLimit>"`
                * Filter out `apiStages` section of the response according to provided `RestApiId`, `RestApiGwStageName`, `RestApiGwResourcePath`, `RestApiGwHttpMethod` values and return `burstLimit` and `rateLimit` from `throttle` section
        * if `stageName` is null
            * Execute https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/apigateway.html#APIGateway.Client.update_usage_plan with the following parameters:
                * `usagePlanId`= `RestApiGwUsagePlanId`
                * `patchOperations`=`op="replace",path="/throttle/rateLimit",value="<newRateLimit>",op="replace",path="/throttle/burstLimit",value="<newBurstLimit>"`
                * Use `throttle` sections in the root of the response and return `burstLimit` and `rateLimit`
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
        * `RestApiGwThrottlingRateRestoredValue` returns `rateLimit`
        * `RestApiGwThrottlingBurstRestoredValue` return `burstLimit`
    * Explanation:
        * Define variables using outputs of `BackupThrottlingConfigurationAndInputs`: 
            * `rateLimit`=`BackupThrottlingConfigurationAndInputs.RestApiGwThrottlingRateOriginalValue`
            * `burstLimit`=`BackupThrottlingConfigurationAndInputs.RestApiGwThrottlingBurstOriginalValue`
            * `usagePlanId`=`BackupThrottlingConfigurationAndInputs.RestApiGwUsagePlanId`
            * `apidId`=`BackupThrottlingConfigurationAndInputs.RestApiId`
            * `stageName`=`BackupThrottlingConfigurationAndInputs.RestApiGwStageName`
            * `resourcePath`=`BackupThrottlingConfigurationAndInputs.RestApiGwResourcePath`, if empty use "*"
            * `httpMethod`=`BackupThrottlingConfigurationAndInputs.RestApiGwHttpMethod`, it empty use "*"
        * if `stageName` is not null
            * Execute https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/apigateway.html#APIGateway.Client.update_usage_plan with the following parameters:
                * `usagePlanId`= `RestApiGwUsagePlanId`
                * `patchOperations`=`op="replace",path="/apiStages/<apidId:stageName>/throttle/<resourcePath>/<httpMethod>/rateLimit",value="<rateLimit>",op="replace",path="/apiStages/<apidId:stageName>/throttle/<resourcePath>/<httpMethod>/burstLimit",value="<burstLimit>"`
                * Filter out `apiStages` section of the resposne according to provided `RestApiId`, `RestApiGwStageName`, `RestApiGwResourcePath`, `RestApiGwHttpMethod` values and return `burstLimit` and `rateLimit` from `throttle` section
        * if `stageName` is null
            * Execute https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/apigateway.html#APIGateway.Client.update_usage_plan with the following parameters:
                * `usagePlanId`= `RestApiGwUsagePlanId`
                * `patchOperations`=`op="replace",path="/throttle/rateLimit",value="<rateLimit>",op="replace",path="/throttle/burstLimit",value="<burstLimit>"`
                * Use `throttle` sections in the root of the response and return `burstLimit` and `rateLimit`
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
* `BackupThrottlingConfigurationAndInputs.RestApiGwUsagePlanId`
* `BackupThrottlingConfigurationAndInputs.RestApiId`
* `BackupThrottlingConfigurationAndInputs.RestApiGwStageName`
* `BackupThrottlingConfigurationAndInputs.RestApiGwResourcePath`
* `BackupThrottlingConfigurationAndInputs.RestApiGwHttpMethod`
* `BackupThrottlingConfigurationAndInputs.RestApiGwThrottlingRateOriginalValue` - original value of throttling rate
* `BackupThrottlingConfigurationAndInputs.RestApiGwThrottlingBurstOriginalValue` - original value of throttling burst


if `IsRollback`:
* `RollbackPreviousExecution.RestApiGwThrottlingRateRestoredValue`
* `RollbackPreviousExecution.RestApiGwThrottlingBurstRestoredValue`

if not `IsRollback`:
* `SetThrottlingConfiguration.RestApiGwThrottlingRateNewValue` - new value of throttling rate
* `SetThrottlingConfiguration.RestApiGwThrottlingBurstNewValue` - new value of throttling burst