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
Users can run the script with `IsRollback` and `PreviousExecutionId` to rollback changes from the previous run. 

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
        * `IsRollback` it false, continue with `BackupLambdaSecurityGroupsConfigurationAndInputs` step
1. `RollbackPreviousExecution`
    * Type: aws:executeScript
    * Inputs:
        * `PreviousExecutionId`
        * `LambdaARN`
    * Outputs:
        * `SecurityGroupListRestoredValue`
    * Explanation:
        * Get values from previous execution by `PreviousExecutionId`
          * `previousLambdaArn` = `BackupLambdaSecurityGroupsConfigurationAndInputs.LambdaARN` 
          * `previousSecurityGroups` = `BackupLambdaSecurityGroupsConfigurationAndInputs.SecurityGroupList` 
        * Check if `previousLambdaArn` equals to `LambdaARN` if not raise an error
        * Execute [update_function_configuration](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/lambda.html#Lambda.Client.update_function_configuration). 
          * Parameters
            * `FunctionName`=`LambdaARN`
            * `VpcConfig`={"SecurityGroupIds":`Backup.SecurityGroupList`}
          * Return `.VpcConfig.SecurityGroupIds[]`
    * isEnd: true
1. `BackupLambdaSecurityGroupsConfigurationAndInputs`
    * Type: aws:executeScript
    * Inputs:
        * `SecurityGroupId`
        * `LambdaARN`
    * Outputs:
        * `SecurityGroupList`
        * `LambdaARN` - backups input
    * Explanation:
        * Query get the list of security groups attached to lambda [get_function_configuration](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/lambda.html#Lambda.Client.get_function_configuration). Parameters
          * `FunctionName`=`LambdaARN`
        * Validate if given `SecurityGroupId` is in the list. If not, throw an error.
        * Return list of taken SGs  
        * Return `LambdaARN`
1. `RemoveSecurityGroupAssignment`
    * Type: aws:executeScript
    * Inputs:
        * `SecurityGroupId`
    * Outputs:
        * `SecurityGroupListUpdatedValue`
    * Explanation:
        * Derive `SecurityGroupListUpdatedValue` from removing `SecurityGroupId` from `BackupLambdaSecurityGroupsConfigurationAndInputs.SecurityGroupList` 
        * Execute [update_function_configuration](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/lambda.html#Lambda.Client.update_function_configuration). Parameters
          * `FunctionName`=`LambdaARN`
          * `VpcConfig`={"SecurityGroupIds":`SecurityGroupListUpdatedValue`}
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
    * Outputs: 
        * `SecurityGroupListRestoredValue`
    * Explanation:
        * Execute [update_function_configuration](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/lambda.html#Lambda.Client.update_function_configuration). 
          * Parameters
            * `FunctionName`=`LambdaARN`
            * `VpcConfig`={"SecurityGroupIds":`BackupLambdaSecurityGroupsConfigurationAndInputs.SecurityGroupList`}
          * Return `.VpcConfig.SecurityGroupIds[]`
1. `AssertAlarmToBeGreen`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `SyntheticAlarmName`
    * Outputs: none
    * Explanation:
        * Wait for `SyntheticAlarmName` alarm to be `OK` for 600 seconds
    * isEnd: true
 
## Outputs
* `BackupLambdaSecurityGroupsConfigurationAndInputs.SecurityGroupList`: a list of Security Groups that has been assigned to ENIs of the current Lambda VPC configuration
* `BackupLambdaSecurityGroupsConfigurationAndInputs.LambdaARN`

if `IsRollback`:
* `RollbackPreviousExecution.SecurityGroupListRestoredValue`

if not `IsRollback`:
* `RemoveSecurityGroupAssignment.SecurityGroupListUpdatedValue`: an updated list of Security groups (given `SecurityGroupId` has been removed)
* `RollbackChanges.SecurityGroupListRestoredValue`