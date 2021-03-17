# Id
lambda:test:break_security_group:2020-09-21

## Intent
Test Lambda behavior after breaking security group

## Type
AZ Outage Test

## Risk
High

## Requirements
* Existing Lambda Function
* Lambda has VPC configuration

## Permission required for AutomationAssumeRole
* lambda:GetFunctionConfiguration
* lambda:UpdateFunctionConfiguration
* cloudwatch:DescribeAlarms

## Supports Rollback
Yes. The script backups existing Security Groups assigned and restores it when the specified alarms fires.
Users can run the script with `IsRollback` and `PreviousExecutionId` to roll backup changes from the previous run. 

## Inputs

### `AutomationAssumeRole`
  * type: String
  * description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf
### `SyntheticAlarmName`:
  * type: String
  * description: (Required) Alarm which should be green after test
### `LambdaARN`
  * type: String
  * description: (Required) The ARN of the Lambda function
### `SecurityGroupId`:
  * type: string
  * description: (Required) The identifier of the security group that allows communication between give Lambda function and another AWS Service (e.g. DynamoDB, RDS, and etc.)
### `IsRollback`:
  * type: Boolean
  * description: (Optional) Run rollback step of the given previous execution (parameter `PreviousExecutionId`)
  * default: False
### `PreviousExecutionId`:
  * type: Integer
  * description: (Optional) The id of previous execution of the current script
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
    * Type: aws:executescript
    * Inputs:
        * `PreviousExecutionId`
    * Outputs:
    * Explanation:
        * Get value of `Backup.SecurityGroupList` from `PreviousExecutionId`
        * Execute [update_function_configuration](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/lambda.html#Lambda.Client.update_function_configuration). Parameters
          * `FunctionName`=`LambdaARN`
          * `VpcConfig`={"SecurityGroupIds":`Backup.SecurityGroupList`}
        * isEnd: true
1. `Backup`
    * Type: aws:executeScript
    * Inputs:
        * `SecurityGroupId`
        * `LambdaArn`
    * Outputs:
        * `SecurityGroupList`
    * Explanation:
        * Query get the list of security groups attached to lambda [get_function_configuration](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/lambda.html#Lambda.Client.get_function_configuration). Parameters
          * `FunctionName`=`LambdaARN`
        * Validate if given `SecurityGroupId` is in the list. If not, throw an error.
        * Return list of taken SGs  
1. `RemoveSecurityGroupAssigment`
    * Type: aws:executeScript
    * Inputs:
        * `SecurityGroupId`
        * `Backup.SecurityGroupList`
    * Outputs:
        * `UpdatedSecurityGroupList`
    * Explanation:
        * Derrive `UpdatedSecurityGroupList` from removing `SecurityGroupId` from `Backup.SecurityGroupList` 
        * Execute [update_function_configuration](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/lambda.html#Lambda.Client.update_function_configuration). Parameters
          * `FunctionName`=`LambdaARN`
          * `VpcConfig`={"SecurityGroupIds":`UpdatedSecurityGroupList`}
    * OnFailure: step: `RollbackChanges` 
1. `AssertAlarmToBeRed`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `SyntheticAlarmName`
    * Outputs: none
    * Explanation:
        * Wait for `SyntheticAlarmName` alarm to be `ALARM` for 600 seconds
    * OnFailure: step: `RollbackChanges` 
1. `RollbackChanges`
    * Type: aws:executeScript
    * Inputs:
        * `SecurityGroupId`
        * `Backup.SecurityGroupList`
    * Outputs: None
    * Explanation:
        * Execute [update_function_configuration](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/lambda.html#Lambda.Client.update_function_configuration). Parameters
          * `FunctionName`=`LambdaARN`
          * `VpcConfig`={"SecurityGroupIds":`Backup.SecurityGroupList`}
1. `AssertAlarmToBeGreen`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `SyntheticAlarmName`
    * Outputs: none
    * Explanation:
        * Wait for `SyntheticAlarmName` alarm to be `OK` for 600 seconds
    * isEnd: true
 
## Outputs
`Backup.SecurityGroupList`: a list of Security Groups that has been assgined to ENIs of the current Lambda VPC configuration
`RemoveSecurityGroupAssigment.UpdatedSecurityGroupList`: an updated list of Security groups (given `SecurityGroupId` has been removed)
