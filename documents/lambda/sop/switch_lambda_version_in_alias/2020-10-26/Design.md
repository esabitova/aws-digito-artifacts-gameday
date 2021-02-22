# Id
lambda:sop:switch_lambda_version_in_alias:2020_10_26

## Intent
Switch Alias of Lambda functions to another version

## Type
Software Outage SOP

## Risk
Medium

## Requirements
* Existing Lambda Function

## Permission required for AutomationAssumeRole
* lambda:UpdateFunctionCode

## Supports Rollback
No

## Inputs
### `AliasName`:
    type: String
    description: (Required) The existing alias of the Lambda function
### `LambdaARN`:
    type: String
    description: (Required) The Lambda ARN
### `LambdaVersion`:
    type: String
    description: (Required) The Lambda version
### `AutomationAssumeRole`:
    type: String
    description: (Optional) The ARN of the role that allows Automation to perform the actions on your behalf. If no role is specified, Systems Manager Automation uses your IAM permissions to run this document.
    default: ''

## Details of SSM Document steps:
1. `SwitchVersion`
    * Type: aws:executeAwsApi
    * Inputs:
        * `AliasName`
        * `LambdaARN`
        * `LambdaVersion`
    * Outputs:
        * `AliasArn`: The alias arn from API response
    * Explanation:
        * Execute [update_alias](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/lambda.html#Lambda.Client.update_alias). Parameters:
          * `FunctionName`='`LambdaARN`'
          * `Name `=`AliasName`
          * `FunctionVersion `=`LambdaVersion`
 
## Outputs
`SwitchVersion.AliasArn`
