# Id
lambda:sop:change_provisioned_concurrency:2020_10_26

## Intent
Warm up Lambda function by changing `ProvisionedConcurrentExecutions` value for the Lambda function

## Type
Software Outage SOP

## Risk
Medium

## Requirements
* Existing Lambda Function

## Permission required for AutomationAssumeRole
* lambda:PutProvisionedConcurrencyConfig

## Supports Rollback
No

## Inputs

### `AutomationAssumeRole`
  * type: String
  * description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf
### `LambdaARN`
  * type: String
  * description: (Required) The ARN of the Lambda function
### `ProvisionedConcurrentExecutions`:
  * type: Integer
  * description: (Required) New ProvisionedConcurrency value
### `LambdaQualifier`
  * type: String
  * description: (Required) The version number or alias name

## Details of SSM Document steps:
1. `SetProvisionedConcurrency`
    * Type: aws:executeAwsApi
    * Inputs:
        * `LambdaARN`
        * `ProvisionedConcurrentExecutions`
        * `LambdaQualifier`
    * Outputs: 
        * `NewValueOfProvisionedConcurrency`: the value of `AllocatedProvisionedConcurrentExecutions` property in the response
    * Explanation:
        * Execute [put_provisioned_concurrency_config](https://docs.aws.amazon.com/lambda/latest/dg/API_PutProvisionedConcurrencyConfig.html). Parameters:
          * `FunctionName`='`LambdaARN`'
          * `ProvisionedConcurrentExecutions`=`ProvisionedConcurrentExecutions`
          * `Qualifier`='`LambdaQualifier`'
        * Return `ProvisionedConcurrentExecutions` as `NewValueOfProvisionedConcurrency`
 
## Outputs
`NewValueOfProvisionedConcurrency` - the new value of provisioned concurrency
