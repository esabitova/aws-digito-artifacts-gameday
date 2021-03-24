# Id

sqs:test:block_delete_message:2021-03-09

## Intent

Test behavior when messages are not deleted from a specific queue

## Type

Software Outage Test

## Risk

High

## Requirements

* Existing queue
* Existing alarm the queue

## Permission required for AutomationAssumeRole

* cloudwatch:DescribeAlarms
* sqs:GetQueueAttributes
* sqs:SetQueueAttributes

## Supports Rollback

Yes. The script performs rollback of SQSPolicy. Users can run the script with IsRollback and PreviousExecutionId to purge dead letter queue from previous run.

## Inputs

### `QueueURL`

* description: (Required) The URL of the queue
* type: String

### `SQSUserErrorAlarmName`

* type: String
* description: (Required) Alarm which should be red after injection of the failure and green after the rollback process in the end of the test.

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
        * `Policy`: The backup SQS Policy
    * Explanation:
        * Get values of SSM Document output parameters from the previous execution using `PreviousExecutionId`:
            * `Policy`
1. `RollbackPreviousExecution`
    * Type: aws:executeAutomation
    * Inputs:
        * `PrepareRollbackOfPreviousExecution.Policy`
    * Outputs:
        * `ActualPolicy`
    * Explanation:
        * Update the policy by calling [set_queue_attributes](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs.html#SQS.Client.set_queue_attributes)
1. `AssertAlarmToBeGreenBeforeTest`
   * Type: aws:assertAwsResourceProperty
1. `BackupCurrentExecution`
    * Type: aws:executeAwsApi
    * Inputs:
        * `QueueURL`
    * Outputs:
        * `Policy`
        * `QueueArn`
    * Explanation:
        * Get `Policy` field from the response of method
          call [get_queue_attributes](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs.html#SQS.Client.get_queue_attributes)
1. `GetPolicyWithDenyOnDeleteMessageAction`
    * Type: aws:executeScript
    * Inputs:
        * `Policy`
    * Outputs:
        * `Policy`
        * `DenyPolicyStatementSid`
        * `PolicySid`
    * Explanation:
        * Add deny on "Principal": "*" for sqs:DeleteMessage action
1. `UpdatePolicy`
    * Type: aws:executeAwsApi
    * Inputs:
        * `QueueURL`
        * `GetPolicyWithDenyOnDeleteMessageAction.Policy`
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
        * `BackupCurrentExecution.Policy`
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
	 