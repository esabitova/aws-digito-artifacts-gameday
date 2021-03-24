# Id

api-gw:sop:change_throttling_settings_rest:2020-10-26

## Intent
Change throttling settings for REST API Gateway. The script checks if throttling rate or burst going to be changed on more than 50%. If so, raises an error. Customers have an option to disable this validation by passing `ForceExecution` parameter or change throttling burst and rate with smaller increments


## Type
Software Outage SOP

## Risk
Medium

## Requirements
* Existing REST API Gateway

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
### `RestApiGwThrottlingRate`:
  * type: Integer
  * description: (Required) The value of throttling rate (requests per second)
### `RestApiGwThrottlingBurst`:
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
        * `ForceExecution` it true, continue with `SetThrottlingConfiguration` step
        * `ForceExecution` it false, continue with `ValidateInputs` step
1. `ValidateInputs`
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
        * `RestApiGwUsagePlanId`
        * `RestApiId`
        * `RestApiGwStageName`
        * `RestApiGwResourcePath`
        * `RestApiGwHttpMethod`
        * `RestApiGwThrottlingRateOriginalValue` - returns `originalRateLimit`
        * `RestApiGwThrottlingBurstOriginalValue` - returns `originalBurstLimit`
        * `RestApiGwThrottlingRate`
        * `RestApiGwThrottlingBurst`
    * Explanation:
        * Execute https://docs.aws.amazon.com/cli/latest/reference/apigateway/get-usage-plan.html
            * if `RestApiGwStageName` is not null:
                * Filter out `apiStages` section of the response according to provided `RestApiId`, `RestApiGwStageName`, `RestApiGwResourcePath`, `RestApiGwHttpMethod` values and return `originalBurstLimit` and `originalRateLimit` from `throttle` section
            * if `RestApiGwStageName` is null:
                * Use `throttle` sections in the root or the response and return `originalBurstLimit` and `originalRateLimit`
        * Check if `abs(RestApiGwThrottlingBurst - originalBurstLimit) > RestApiGwThrottlingBurst*0.5`, if True raise an error saying that the burst rate is going to be increased on more than 50%, please use smaller increments or use `ForceExecution` parameter to disable validation.
        * Check if `abs(RestApiGwThrottlingRate - originalRateLimit) > RestApiGwThrottlingRate*0.5`, if True raise an error saying that the throttling rate is going to be increased on more than 50%, please use smaller increments or use `ForceExecution` parameter to disable validation.
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
        * Check if Throttle Rate less than Account Level Quota
          * Get `ThrottleRateAccountQuotaValue` by executing https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/service-quotas.html#ServiceQuotas.Client.get_service_quota
            * Parameters:
              * `ServiceCode`=`apigateway`
              * `QuotaCode`=`L-8A5B8E43`
            * Return `Quota.Value`
          * Check if `RestApiGwThrottlingRate` greater than quota value, if so throw a human readable error with the quota and given value
        * Check if Throttle Burst less than Account Level Quota
          * Get `BurstRateAccountQuotaValue` by executing https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/service-quotas.html#ServiceQuotas.Client.get_service_quota
            * Parameters:
              * `ServiceCode`=`apigateway`
              * `QuotaCode`=`L-CDF5615A`
            * Return `Quota.Value`
          * Check if `RestApiGwThrottlingBurst` greater than quota value, if so throw a human readable error with the quota and given value
        * if `stageName` is not null
            * Execute https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/apigateway.html#APIGateway.Client.update_usage_plan
              * Parameters:
                * `usagePlanId`= `RestApiGwUsagePlanId`
                * `patchOperations`=`op="replace",path="/apiStages/<apidId:stageName>/throttle/<resourcePath>/<httpMethod>/rateLimit",value="<newRateLimit>",op="replace",path="/apiStages/<apidId:stageName>/throttle/<resourcePath>/<httpMethod>/burstLimit",value="<newBurstLimit>"`
              * Filter out `apiStages` section of the response according to provided `RestApiId`, `RestApiGwStageName`, `RestApiGwResourcePath`, `RestApiGwHttpMethod` values and return `burstLimit` and `rateLimit` from `throttle` section
        * if `stageName` is null
            * Execute https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/apigateway.html#APIGateway.Client.update_usage_plan with the following parameters:
                * `usagePlanId`= `RestApiGwUsagePlanId`
                * `patchOperations`=`op="replace",path="/throttle/rateLimit",value="<newRateLimit>",op="replace",path="/throttle/burstLimit",value="<newBurstLimit>"`
                * Use `throttle` sections in the root of the response and return `burstLimit` and `rateLimit`
    * isEnd: true

## Outputs
* `SetThrottlingConfiguration.NewThrottlingBurstLimitValue`
* `SetThrottlingConfiguration.NewThrottlingRateLimitValue`

if not `ForceExecution`:
* `ValidateInputs.RestApiGwUsagePlanId`
* `ValidateInputs.RestApiId`
* `ValidateInputs.RestApiGwStageName`
* `ValidateInputs.RestApiGwResourcePath`
* `ValidateInputs.RestApiGwHttpMethod`
* `ValidateInputs.RestApiGwThrottlingRateOriginalValue`
* `ValidateInputs.RestApiGwThrottlingBurstOriginalValue`
* `ValidateInputs.RestApiGwThrottlingRate`
* `ValidateInputs.RestApiGwThrottlingBurst`
