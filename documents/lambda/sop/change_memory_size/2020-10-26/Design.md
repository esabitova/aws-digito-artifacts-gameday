# Id
lambda:sop:change_memory_size:2020_10_26

## Intent
Change Memory size 

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
### `NewMemorySizeValue`:
  * type: Integer
  * description: (Required) New RAM value in Megabytes  (128 MB — 10,240 MB)

## Details of SSM Document steps:
1. `SetMemorySize`
    * Type: aws:executeAwsApi
    * Inputs:
        * `LambdaARN`
        * `NewMemorySizeValue`
    * Outputs: 
        * `NewMemorySizeValue`
    * Explanation:
        * Execute [update_function_configuration](https://docs.aws.amazon.com/lambda/latest/dg/API_UpdateFunctionConfiguration.html). Parameters:
          * `FunctionName`='`LambdaARN`'
          * `MemorySize`=`NewMemorySizeValue`
        * Return `NewMemorySizeValue` from the previous step response `MemorySize`
 
## Outputs
`SetMemorySize.NewMemorySizeValue` - the new value of RAM assigned to the given Lambda function
