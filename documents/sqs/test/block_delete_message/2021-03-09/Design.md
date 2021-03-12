# Id

sqs:test:block_delete_message:2021-03-09

## Intent

Test SQS behavior after blocking sqs:DeleteMessage for the specified queue

## Type

Software Outage Test

## Risk

Low

## Requirements

* Existing queue 
* Existing alarm the queue

## Permission required for AutomationAssumeRole

* cloudwatch:DescribeAlarms
* sqs:GetQueueAttributes
* sqs:SetQueueAttributes

## Supports Rollback

Yes. The script performs rollback of SQSPolicy. Users can run the script with IsRollback and PreviousExecutionId to purge dead letter queue
from previous run.

## Inputs

### `QueueURL`

* description: (Required) The URL of the queue
* type: String

### `SQSUserErrorAlarmName`

* type: String
* description: (Optional) Alarm which should be red after injection of the failure and green after the rollback process in the end of the test.
* default: 'ApproximateAgeOfOldestMessageMaximum'

### `AlarmWaitTimeout`

* type: Integer
* description: (Required) Alarm wait timeout
* default: 300 (seconds)

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
        * `IsRollback` it true, continue with `PrepareRollbackOfPreviousExecution` step
        * `IsRollback` it false, continue with `BackupCurrentExecution` step
1. `PrepareRollbackOfPreviousExecution`
    * Type: aws:executeScript
    * Inputs:
        * `PreviousExecutionId`
    * Outputs:
        * `SQSPolicy`: The backup SQS Policy
    * Explanation:
        * Get values of SSM Document input parameters from the previous execution using `PreviousExecutionId`:
            * `SQSPolicy`
1. `RollbackPreviousExecution`
    * Type: aws:executeAutomation
    * Inputs:
        * `PrepareRollbackOfPreviousExecution.SQSPolicy`
    * Outputs:
        * `ActualPolicy`
    * Explanation:
        * Update the policy by calling [set_queue_attributes](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs.html#SQS.Client.set_queue_attributes)
1. `BackupCurrentExecution`
    * Type: aws:executeAwsApi
    * Inputs:
        * `QueueURL`
    * Outputs:
        * `SQSPolicy`
    * Explanation:
        * Get `Policy` field from the response of method
          call [get_queue_attributes](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs.html#SQS.Client.get_queue_attributes)
1. `RemoveDeleteMessageAction`
    * Type: aws:executeScript
    * Inputs:
        * `SQSPolicy`
    * Outputs:
        * `SQSPolicy`
    * Explanation:
        * Remove `sqs:DeleteMessage` action from the input `SQSPolicy`
1. `UpdatePolicy`
    * Type: aws:executeAwsApi
    * Inputs:
        * `QueueURL`
        * `RemoveDeleteMessageAction.SQSPolicy`
    * Outputs: None
    * Explanation:
        * Update the policy by calling [set_queue_attributes](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs.html#SQS.Client.set_queue_attributes)
    * OnFailure: step: RollbackCurrentExecution
1. `AssertAlarmToBeRed`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `SQSUserErrorAlarmName`
    * Outputs: none
    * Explanation:
        * Wait for the alarm to be in `ALARM` state
    * OnFailure: step: RollbackCurrentExecution
1. `RollbackCurrentExecution`
    * Type: aws:executeAwsApi
    * Inputs:
        * `QueueURL`
        * `BackupCurrentExecution.SQSPolicy`
    * Outputs:
        * `ActualPolicy`
    * Explanation:
        * Update the policy by calling [set_queue_attributes](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs.html#SQS.Client.set_queue_attributes)
1. `AssertAlarmToBeGreen`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `SQSUserErrorAlarmName`
    * Outputs: none
    * Explanation:
        * Wait for the alarm to be in `OK` state

## Outputs

No.
	 