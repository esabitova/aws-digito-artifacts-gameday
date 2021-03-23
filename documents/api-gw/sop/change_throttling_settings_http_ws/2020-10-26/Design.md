# Id

api-gw:sop:change_throttling_settings_http_ws:2020-10-26

## Intent
Change throttling settings for HTTP or WEBSOCKET types of API. The script checks if throttling rate or burst going to be changed on more than 50%. If so, raises an error. Customers have an option to disable this validation by passing `ForceExecution` parameter or change throttling burst and rate with smaller increments


## Type
Software Outage SOP

## Risk
Medium

## Requirements
* Existing HTTP or WEBSOCKET API Gateway 

## Permission required for AutomationAssumeRole
* apigateway:GET
* apigateway:PUT
* servicequotas:GetServiceQuota

## Supports Rollback
No.

## Inputs
### `AutomationAssumeRole`
  * type: String
  * description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf
### `HttpWsApiGwId`
  * type: String
  * description: (Required) The ID of the HTTP or WEBSOCKET API Gateway
### `HttpWsApiGwStageName`
  * type: String
  * description: (Required) The name of the Stage which throttling settings should be applied to
### `HttpWsApiGwThrottlingRate`:
  * type: Integer
  * description: (Required) The value of throttling rate (requests per second)
### `HttpWsApiGwThrottlingBurst`:
  * type: Integer
  * description: (Required) The value of throttling rate (requests)
### `ForceExecution`:
  * type: Boolean
  * description: (Optional) If True, validations will be skipped
  * default: False

## Details
1. `CheckIfForceExecutionIsSet`
    * Type: aws:branch
    * Inputs:
        * `ForceExecution`
    * Outputs: none
    * Explanation:
        * `ForceExecution` it true, continue with `ChangeThrottlingConfiguration` step
        * `ForceExecution` it false, continue with `ValidateInputs` step
1. `ValidateInputs`
    * Type: aws:executeScript
    * Inputs:
        * `HttpWsApiGwId`
        * `HttpWsApiGwStageName`
        * `HttpWsApiGwThrottlingRate`
        * `HttpWsApiGwThrottlingBurst`
    * Outputs: 
        * `HttpWsApiGwId`
        * `HttpWsApiGwStageName`
        * `HttpWsApiGwThrottlingRate`
        * `HttpWsApiGwThrottlingBurst`
        * `HttpWsApiGwThrottlingRateOriginalValue` - returns `originalRateLimit`
        * `HttpWsApiGwThrottlingBurstOriginalValue` - returns `originalBurstLimit`
    * Explanation:
        * Execute https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/apigatewayv2.html#ApiGatewayV2.Client.get_stage with the following parameters:
            * `ApiId`=`HttpWsApiGwId`
            * `StageName`=`HttpWsApiGwStageName`
          * Parse output of the execution to take `RouteSettings.ThrottlingBurstLimit` as `originalBurstLimit` and `RouteSettings.ThrottlingRateLimit` as `originalRateLimit`. Use `DefaultRouteSettings` if `RouteSettings` does not exist
        * Check if `abs(HttpWsApiGwThrottlingBurst - originalBurstLimit) > HttpWsApiGwThrottlingBurst*0.5`, if True raise an error saying that the burst rate is going to be increased on more than 50%, please use smaller increments or use `ForceExecution` parameter to disable validation.
        * Check if `abs(HttpWsApiGwThrottlingRate - originalRateLimit) > HttpWsApiGwThrottlingRate*0.5`, if True raise an error saying that the throttling rate is going to be increased on more than 50%, please use smaller increments or use `ForceExecution` parameter to disable validation.
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
        * Check if Throttle Rate less than Account Level Quota
          * Get `ThrottleRateAccountQuotaValue` by executing https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/service-quotas.html#ServiceQuotas.Client.get_service_quota
            * Parameters:
              * `ServiceCode`=`apigateway`
              * `QuotaCode`=`L-8A5B8E43`
            * Return `Quota.Value`
          * Check if `HttpWsApiGwThrottlingRate` greater than quota value, if so throw a human readable error with the quota and given value
        * Check if Throttle Burst less than Account Level Quota
          * Get `BurstRateAccountQuotaValue` by executing https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/service-quotas.html#ServiceQuotas.Client.get_service_quota
            * Parameters:
              * `ServiceCode`=`apigateway`
              * `QuotaCode`=`L-CDF5615A`
            * Return `Quota.Value`
          * Check if `HttpWsApiGwThrottlingBurst` greater than quota value, if so throw a human readable error with the quota and given value
        * Define variables using values:
            * `rate`=`HttpWsApiGwThrottlingRate`
            * `burst`=`HttpWsApiGwThrottlingBurst`
            * `apiGwId`=`HttpWsApiGwId`
            * `stageName`=`HttpWsApiGwStageName`
        * Execute https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/apigatewayv2.html#ApiGatewayV2.Client.update_stage 
          * Parameters:
            * `ApiId`=`apiGwId`
            * `StageName`=`stageName`
            * `RouteSettings`={"ThrottlingBurstLimit":"`burst`", "ThrottlingRateLimit":"`rate`"}
          *  Parse output of the execution to take `RouteSettings.ThrottlingBurstLimit` and `RouteSettings.ThrottlingRateLimit`. Use `DefaultRouteSettings` if `RouteSettings` does not exist
    * isEnd: true 

## Outputs
* `ChangeThrottlingConfiguration.HttpWsApiGwThrottlingRateNewValue`
* `ChangeThrottlingConfiguration.HttpWsApiGwThrottlingBurstNewValue`

if not `ForceExecution`:
* `ValidateInputs.HttpWsApiId`
* `ValidateInputs.HttpWsApiGwStageName`
* `ValidateInputs.HttpWsApiGwThrottlingRateOriginalValue`
* `ValidateInputs.HttpWsApiGwThrottlingBurstOriginalValue`
* `ValidateInputs.HttpWsApiGwThrottlingRate`
* `ValidateInputs.HttpWsApiGwThrottlingBurst`
