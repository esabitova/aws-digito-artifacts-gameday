# Id

api-gw:sop:change_quota_limit:2020-10-26

## Intent
Change quota limit of REST API Gateway. It also validates inputs and raises an error if Quota limit is going to be increased/decreased on more than 50%. Customer have an option to skip this validation using  `ForceExecution` parameter or execute the current SOP several times with smaller increments


## Type
Software Outage SOP

## Risk
Medium

## Requirements
* Existing API Gateway REST API

## Permission required for AutomationAssumeRole
* apigateway:GET
* apigateway:PUT

## Supports Rollback
No

## Inputs
### `AutomationAssumeRole`
  * type: String
  * description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf
### `RestApiGwUsagePlanId`
  * type: String
  * description: (Required) The ID of REST API Gateway usage plan
### `RestApiGwQuotaLimit`:
  * type: Integer
  * description: (Required) The value of quota (requests per period).
### `RestApiGwQuotaPeriod`:
  * type: String
  * description: (Required) The value of quota period. Possible values: DAY, WEEK, MONTH. 
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
        * `ForceExecution` it true, continue with `SetQuotaConfiguration` step
        * `ForceExecution` it false, continue with `ValidateInputs` step
1. `ValidateInputs`
    * Type: aws:executeScript
    * Inputs:
        * `RestApiGwUsagePlanId`
        * `RestApiGwQuotaLimit`
        * `RestApiGwQuotaPeriod`
    * Outputs: 
        * `RestApiGwQuotaLimitOriginalValue` returns `currentLimit`
        * `RestApiGwQuotaPeriodOriginalValue` returns `currentPeriod`
        * `RestApiGwQuotaLimit` returns corresponding input
        * `RestApiGwQuotaPeriod` returns corresponding input
    * Explanation:
        * Get the current settings of the usage plan https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/apigateway.html#APIGateway.Client.get_usage_plan
            * Parameters:
                * `usagePlanId`= `RestApiGwUsagePlanId`
            * Use `quota` sections in the root of the response and return `currentLimit` and `currentPeriod`
        * `convertedCurrentLimit`= Convert `currentLimit` to `DAY` value. e.g. if `currentPeriod` is `MONTH` then `currentLimit`/30.0 if `WEEK` then `currentLimit`/7.0
        * `convertedNewLimit`= Convert `RestApiGwQuotaLimit` to `DAY` value. e.g. if `RestApiGwQuotaPeriod` is `MONTH` then `RestApiGwQuotaLimit`/30.0 if `WEEK` then `RestApiGwQuotaLimit`/7.0
        * Check if `abs(convertedCurrentLimit - convertedNewLimit) > convertedCurrentLimit*0.5`, if True raise an error saying that the quota is going to be increased on more than 50%, please use smaller increments or use `ForceExecution` parameter to disable validation.
        * Define variables
            * `quota`=`RestApiGwQuotaLimit`
            * `quotaPeriod`=`RestApiGwQuotaPeriod`
            * `usagePlanId`=`RestApiGwUsagePlanId`
        * Execute https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/apigateway.html#APIGateway.Client.update_usage_plan 
            * Parameters:
                * `usagePlanId`= `RestApiGwUsagePlanId`
                * `patchOperations`=`op="replace",path="/quota/limit",value="<quota>",op="replace",path="/quota/period",value="<quotaPeriod>"`
            * Use `quota` sections in the root of the response and return `limit` and `period`
    * next: step:SetQuotaConfiguration
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
    * isEnd: true

## Outputs
* `SetQuotaConfiguration.RestApiGwQuotaLimitNewValue` - new value of quota limit
* `SetQuotaConfiguration.RestApiGwQuotaPeriodNewValue` - new value of quota period

if not `ForceExecution`:
* `ValidateInputs.RestApiGwQuotaLimitOriginalValue`
* `ValidateInputs.RestApiGwQuotaPeriodOriginalValue`
* `ValidateInputs.RestApiGwQuotaLimit`
* `ValidateInputs.RestApiGwQuotaPeriod`