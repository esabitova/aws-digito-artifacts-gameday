# Id
lambda:sop:change_concurrency_limit:2020-10-26

## Intent
Test Lambda behavior when hitting ReservedConcurrentExecutions value 

## Type
Software Outage SOP

## Risk
Medium

## Requirements
* Existing Lambda Function

## Permission required for AutomationAssumeRole
* lambda:PutFunctionConcurrency
* lambda:ListFunctions
* lambda:GetFunctionConcurrency
* lambda:PutFunctionConcurrency
* servicequotas:ListAWSDefaultServiceQuotas
* servicequotas:ListServiceQuotas

## Supports Rollback
No

## Inputs
### `AutomationAssumeRole`
  * type: String
  * description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf
### `LambdaARN`
  * type: String
  * description: (Required) The ARN of the Lambda function
### `NewReservedConcurrentExecutions`:
  * type: Integer
  * description: (Required) New reserved concurrent executions
  * default: 0

## Details of SSM Document steps:
1. `CheckConcurrentExecutionsQuota`
    * Type: aws:executeScript
    * Inputs:
        * `LambdaARN`
    * Outputs:
        * `ConcurrentExecutionsQuota`: The current concurrency quota for Region-Account combination
    * Explanation:
        * Try to get the current applied quota for AWS Lambda Service [list_service_quotas](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/service-quotas.html#ServiceQuotas.Client.list_service_quotas). Search criteria: 
          * Parameter:ServiceCode='lambda'
          * In output search for Quotas[].QuotaCode='L-B99A9384' (the code returned from AWS CLI: `aws service-quotas list-aws-default-service-quotas --service-code lambda`)
          * Take `Quotas[].Value` as an output
        * If the value from previois steps was not found, get the default value of the quota using [get_aws_default_service_quota](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/service-quotas.html#ServiceQuotas.Client.get_aws_default_service_quota)
          * Parameter:ServiceCode='lambda'
          * Parameter:QuotaCode='L-B99A9384'
          * Take `Quota.Value` as an output
1. `CalculateTotalReservedConcurrencyOfExistingLambas`
    * Type: aws:executeScript
    * Inputs: none
    * Outputs:
        * `TotalReservedConcurrency`: Returns total reserved concurrency
    * Explanation:
        * List all Lambda functions [list_functions](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/lambda.html#Lambda.Client.list_functions).
        * Get reserved concurrency for each Lambda function [get_function_concurrency](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/lambda.html#Lambda.Client.get_function_concurrency)
        * Sum all the concurrencies together, return as an output. Exclude the value of Reserved Concurrency of given `LambdaARN`
1. `CheckFeasibility`
    * Type: aws:executeScript
    * Inputs:
      * `CheckConcurrentExecutionsQuota.ConcurrentExecutionsQuota`
      * `CalculateTotalReservedConcurrencyOfExistingLambas.TotalReservedConcurrency`
      * `NewReservedConcurrentExecutions`
    * Outputs:
        * `CanSetReservedConcurrency`: Returns if it's possible to set given value of `NewReservedConcurrentExecutions`
        * `MaximumPossibleReservedConcurrency`: Returns maximum possible value of reserved concurrency
    * Explanation:
        * `MinimumUnreservedConcurrency`=100. From [the documentation](https://docs.aws.amazon.com/lambda/latest/dg/configuration-concurrency.html): "You can reserve up to the Unreserved account concurrency value that is shown, minus 100 for functions that don't have reserved concurrency."
        * Calculate `CanSetReservedConcurrency` as `(CheckConcurrentExecutionsQuota.ConcurrentExecutionsQuota- CalculateTotalReservedConcurrencyOfExistingLambas.TotalReservedConcurrency - NewReservedConcurrentExecutions - MinimumUnreservedConcurrency) > 0`
        * Calculate `MaximumPossibleReservedConcurrency` as `CheckConcurrentExecutionsQuota.ConcurrentExecutionsQuota- CalculateTotalReservedConcurrencyOfExistingLambas.TotalReservedConcurrency - MinimumUnreservedConcurrency`
1. `DesideOnExecution`
    * Type: aws:branch
    * Inputs:
        * `CheckFeasibility.CanSetReservedConcurrency`
    * Outputs: none
    * Explanation:
        * `CheckFeasibility.CanSetReservedConcurrency` it true, continue with `SetReservedConcurrentExecutions` step
        * `CheckFeasibility.CanSetReservedConcurrency` it false, continue with `StopExecution` step
1. `SetReservedConcurrentExecutions`
    * Type: aws:executeScript
    * Inputs:
        * `LambdaARN`
        * `NewReservedConcurrentExecutions`
        * `CheckFeasibility.MaximumPossibleReservedConcurrency`
    * Outputs:
        * `ReservedConcurrencyLeft`: The maximum value of Reserved Concurrency that be spread across other Lamba functions
        * `NewReservedConcurrencyValue`: The new reserved concurrency value for the give Lambda function
    * Explanation:
        * Set `NewReservedConcurrentExecutions` using  [put_function_concurrency](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/lambda.html#Lambda.Client.put_function_concurrency). Parameters:
          * FunctionName='`LambdaARN`',
          * ReservedConcurrentExecutions=`NewReservedConcurrentExecutions`
        * Return `NewReservedConcurrencyValue` from the previous step response `ReservedConcurrentExecutions`
        * Calculate `ReservedConcurrencyLeft` by `(CheckFeasibility.MaximumPossibleReservedConcurrency - NewReservedConcurrentExecutions)`
1. `StopExecution`
    * Type: aws:executeScript
    * Inputs:
        * `CheckFeasibility.MaximumPossibleReservedConcurrency`
    * Outputs:
        * `Error`: human-readable response to customers with `CheckFeasibility.MaximumPossibleReservedConcurrency` value and recommendations
    * Explanation:
        * Returns human-readable response to customers with `CheckFeasibility.MaximumPossibleReservedConcurrency` value and recommendations

## Outputs
* `StopExecution.Error`: human-readable response to customers with `CheckFeasibility.MaximumPossibleReservedConcurrency` value and recommendations
* `CheckFeasibility.MaximumPossibleReservedConcurrency`: Returns maximum possible value of reserved concurrency before the script being executed
* `SetReservedConcurrentExecutions.ReservedConcurrencyLeft`: The maximum value of Reserved Concurrency that be spread across other Lamba functions
* `SetReservedConcurrentExecutions.NewReservedConcurrencyValue`: The new reserved concurrency value for the give Lambda function
* `CheckConcurrentExecutionsQuota.ConcurrentExecutionsQuota`: The current concurrency quota assigned for the AWS Account
