# Id
api-gw:test:throttling-http-ws:2020-09-21

## Intent
Test API Gateway HTTP or Web sockets behavior when hitting throttling threshold  

## Type
Software Outage Test

## Risk
HIGH

## Requirements
* Existing API Gateway HTTP or Web sockets
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
### `HttpWsApiGwId`
  * type: String
  * description: (Required) The ID of the HTTP or WEBSOCKET API Gateway
### `HttpWsApiGwStageName`
  * type: String
  * description: (Required) The name of the Stage which throttling settings should be applied to
### `IsRollback`:
  * type: Boolean
  * description: (Optional) Run rollback step of the given previous execution (parameter `PreviousExecutionId`)
  * default: False
### `PreviousExecutionId`:
  * type: Integer
  * description: (Optional) The id of previous execution of the current script
  * default: 0
### `HttpWsApiGwThrottlingRate`:
  * type: Integer
  * description: (Optional) The value of throttling rate (requests per second)
  * default: 0
### `HttpWsApiGwThrottlingBurst`:
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
        * `IsRollback` it false, continue with `Backup` step
1. `RollbackPreviousExecution`
    * Type: aws:executeScript
    * Inputs:
        * `PreviousExecutionId`
    * Outputs: 
        * `HttpWsApiGwThrottlingRateRestoredValue` - parsed value from the output
        * `HttpWsApiGwThrottlingBurstRestoredValue` - parsed value from the output
    * Explanation:
        * Define variables using values from the previous execution (`PreviousExecutionId`):
            * `rate`=`BackupThrottlingConfiguration.HttpWsApiGwThrottlingRateOriginalValue`
            * `burst`=`BackupThrottlingConfiguration.HttpWsApiGwThrottlingBurstOriginalValue`
            * `apiGwId`=`BackupThrottlingConfiguration.HttpWsApiGwId`
            * `stageName`=`BackupThrottlingConfiguration.HttpWsApiGwStageName`
        * Execute https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/apigatewayv2.html#ApiGatewayV2.Client.update_stage with the following parameters:
            * `ApiId`=`apiGwId`
            * `StageName`=`stageName`
            * `RouteSettings`={"ThrottlingBurstLimit":"`burst`", "ThrottlingRateLimit":"`rate`"}
            *  Parse output of the execution to take `DefaultRouteSettings.RouteSettings.ThrottlingBurstLimit` and `DefaultRouteSettings.RouteSettings.ThrottlingRateLimit`
        * isEnd: true
1. `BackupThrottlingConfiguration`
    * Type: aws:executeAwsApi
    * Inputs:
        * `HttpWsApiGwId`
        * `HttpWsApiGwStageName`
    * Outputs:
        * `HttpWsApiGwThrottlingRateOriginalValue`
        * `HttpWsApiGwThrottlingBurstOriginalValue`
        * `HttpWsApiGwId`
        * `HttpWsApiGwStageName`
    * Explanation:
        * Execute https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/apigatewayv2.html#ApiGatewayV2.Client.update_stage with the following parameters:
            * `ApiId`=`HttpWsApiGwId`
            * `StageName`=`HttpWsApiGwStageName`
            * Parse output of the execution to take `DefaultRouteSettings.RouteSettings.ThrottlingBurstLimit` and `DefaultRouteSettings.RouteSettings.ThrottlingRateLimit`
        * Return parsed values as well as input parameters
1. `ChangeThrottlingConfiguration`
    * Type: aws:executeScript
    * Inputs:
        * `HttpWsApiGwId`
        * `HttpWsApiGwStageName`
        * `HttpWsApiGwThrottlingRate`
        * `HttpWsApiGwThrottlingBurst`
    * Outputs: 
        * `HttpWsApiGwThrottlingRateNewValue` - parsed value from the output
        * `HttpWsApiGwThrottlingBurstNewValue` - parsed value from the output
    * Explanation:
        * Define variables using values:
            * `rate`=`HttpWsApiGwThrottlingRate`
            * `burst`=`HttpWsApiGwThrottlingBurst`
            * `apiGwId`=`HttpWsApiGwId`
            * `stageName`=`HttpWsApiGwStageName`
        * Execute https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/apigatewayv2.html#ApiGatewayV2.Client.update_stage with the following parameters:
            * `ApiId`=`apiGwId`
            * `StageName`=`stageName`
            * `RouteSettings`={"ThrottlingBurstLimit":"`burst`", "ThrottlingRateLimit":"`rate`"}
            *  Parse output of the execution to take `DefaultRouteSettings.RouteSettings.ThrottlingBurstLimit` and `DefaultRouteSettings.RouteSettings.ThrottlingRateLimit`
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
    * Inputs: None
    * Outputs: 
        * `HttpWsApiGwThrottlingRateRestoredValue` - parsed value from the output
        * `HttpWsApiGwThrottlingBurstRestoredValue` - parsed value from the output
    * Explanation:
        * Define variables using values from the current execution:
            * `rate`=`BackupThrottlingConfiguration.HttpWsApiGwThrottlingRateOriginalValue`
            * `burst`=`BackupThrottlingConfiguration.HttpWsApiGwThrottlingBurstOriginalValue`
            * `apiGwId`=`BackupThrottlingConfiguration.HttpWsApiGwId`
            * `stageName`=`BackupThrottlingConfiguration.HttpWsApiGwStageName`
        * Execute https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/apigatewayv2.html#ApiGatewayV2.Client.update_stage with the following parameters:
            * `ApiId`=`apiGwId`
            * `StageName`=`stageName`
            * `RouteSettings`={"ThrottlingBurstLimit":"`burst`", "ThrottlingRateLimit":"`rate`"}
            *  Parse output of the execution to take `DefaultRouteSettings.RouteSettings.ThrottlingBurstLimit` and `DefaultRouteSettings.RouteSettings.ThrottlingRateLimit`
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
* `BackupThrottlingConfiguration.HttpWsApiGwThrottlingRateOriginalValue`
* `BackupThrottlingConfiguration.HttpWsApiGwThrottlingBurstOriginalValue`
* `BackupThrottlingConfiguration.HttpWsApiGwId`
* `BackupThrottlingConfiguration.HttpWsApiGwStageName`

if `IsRollback`:
* `RollbackPreviousExecution.HttpWsApiGwThrottlingRateRestoredValue`
* `RollbackPreviousExecution.HttpWsApiGwThrottlingBurstRestoredValue`

if not `IsRollback`:
* `ChangeThrottlingConfiguration.HttpWsApiGwThrottlingRateNewValue`
* `ChangeThrottlingConfiguration.HttpWsApiGwThrottlingBurstNewValue`
