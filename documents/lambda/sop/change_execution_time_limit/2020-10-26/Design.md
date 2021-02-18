# Id
lambda:sop:change_execution_time_limit:2020_10_26

## Intent
Change execution time limit 

## Type
Software Outage SOP

## Risk
Medium

## Requirements
* Existing Lambda Function

## Permission required for AutomationAssumeRole
* lambda:UpdateFunctionConfiguration

## Supports Rollback
No

## Inputs

### `AutomationAssumeRole`
  * type: String
  * description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf
### `LambdaARN`
  * type: String
  * description: (Required) The ARN of the Lambda function
### `NewTimeoutValue`:
  * type: Integer
  * description: (Required) New Timout value

## Details of SSM Document steps:
1. `SetTimeout`
    * Type: aws:executeAwsApi
    * Inputs:
        * `LambdaARN`
        * `NewTimeoutValue`
    * Outputs: 
        * `NewTimeoutValue`: `Timeout` value from the response
    * Explanation:
        * Execute [update_function_configuration](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/lambda.html#Lambda.Client.update_function_configuration). Parameters:
          * `FunctionName`='`LambdaARN`'
          * `Timeout`=`NewTimeoutValue`

 
## Outputs
`SetTimeout.NewTimeoutValue` - the new value of timeout of the give Lambda function
