# Id
sqs:test:breaking_the_policy_for_sqs:2020-11-27

## Intent
Test behavior when messages cannot be sent to an SQS queue

## Type
SQS queue networking failure

## Risk
High

## Requirements
* Existing SQS queue
* Existing alarm NumberOfMessagesSent

## Permission required for AutomationAssumeRole
* cloudwatch:DescribeAlarms
* sqs:GetQueueAttributes
* sqs:SetQueueAttributes
* sqs:RemovePermission
* sqs:AddPermission

## Supports Rollback

Yes. The script will perform rollback of SQS Policy attribute. Users can run the script with IsRollback and PreviousExecutionId.

## Inputs

### `MainQueueUrl`:
* type: String
* description: (Required) The URL of the main queue

### `NumberOfMessagesSentAlarmName`:
* type: String
* description: (Required) Alarm which should be red after test

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
        * `IsRollback` is true, continue with `PrepareRollbackOfPreviousExecution` step
        * `IsRollback` is false, continue with `AssertAlarmToBeGreenBeforeStart` step
1. `PrepareRollbackOfPreviousExecution`
    * Type: aws:executeScript
    * Inputs:
        * `PreviousExecutionId`
    * Outputs:
        * `Policy`
        * `MainQueueUrl`
    * Explanation:
        * Get values of SSM Document input and output parameters from the previous execution using `PreviousExecutionId`:
            * `MainQueueUrl`
            * `BackupCurrentExecution.Policy`
1. `AssertMainQueueUrl`
    * Type: aws:branch
    * Inputs:
        * `MainQueueUrl`
        * `PrepareRollbackOfPreviousExecution.MainQueueUrl`
    * Outputs: none
    * isEnd: true
    * Explanation:
        * If `PrepareRollbackOfPreviousExecution.MainQueueUrl` is equal to `MainQueueUrl`, continue with `RollbackPreviousExecution` step. If else, stop automation
1. `RollbackPreviousExecution`
    * Type: aws:executeAwsApi
    * Inputs:
        * `PrepareRollbackOfPreviousExecution.MainQueueUrl`
        * `PrepareRollbackOfPreviousExecution.Policy`
    * isEnd: true
    * Explanation:
        * Set `Policy` queue attribute
1. `AssertAlarmToBeGreenBeforeStart`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `NumberOfMessagesSentAlarmName`
    * Explanation:
        * Ensure that `NumberOfMessagesSentAlarmName` alarm is `OK` for 600 seconds
1. `BackupCurrentExecution`
    * Type: aws:executeAwsApi
    * Inputs:
        * `MainQueueUrl`
    * Outputs:
        * `Policy`
    * Explanation:
        * Get `Policy` queue attribute
1. `UpdateQueuePolicy`
    * Type: aws:executeScript
    * Inputs:
        * `MainQueueUrl`
        * `BackupCurrentExecution.Policy`
        * `DenyAction=sqs:SendMessage`
    * Explanation:
        * Add deny rule for `sqs:SendMessage` action into SQS policy
    * OnFailure: step: RollbackCurrentExecution
1. `AssertAlarmToBeRed`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `NumberOfMessagesSentAlarmName`
    * Explanation:
        * Wait for `NumberOfMessagesSentAlarmName` alarm to be `ALARM` for 600 seconds
    * OnFailure: step: RollbackCurrentExecution
1. `RollbackCurrentExecution`
    * Type: aws:executeAwsApi
    * Inputs:
        * `MainQueueUrl`
        * `BackupCurrentExecution.Policy`
    * Explanation:
        * Set `Policy` queue attribute 
1. `AssertAlarmToBeGreen`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `NumberOfMessagesSentAlarmName`
    * Explanation:
        * Wait for `NumberOfMessagesSentAlarmName` alarm to be `OK` for 600 seconds
    * isEnd: true

## Outputs

No.

