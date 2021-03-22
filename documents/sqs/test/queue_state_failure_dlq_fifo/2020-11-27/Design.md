# Id
sqs:test:queue_state_failure_dlq_fifo:2020-11-27

## Intent
Test FIFO SQS behavior after receiving a message maximum allowed times

## Type
Software Outage Test

## Risk
High

## Requirements
* Existing FIFO main queue with enabled dead-letter queue feature
* Existing dead-letter queue
* Existing alarm for dead-letter queue

## Permission required for AutomationAssumeRole
* cloudwatch:DescribeAlarms
* sqs:GetQueueAttributes
* sqs:SetQueueAttributes
* sqs:RemovePermission
* sqs:AddPermission
* sqs:ReceiveMessage
* sqs:SendMessage  
* sqs:PurgeQueue
* ssm:StartAutomationExecution
* ssm:GetAutomationExecution
* iam:PassRole

## Supports Rollback

Yes. The script will perform rollback of main queue attributes: Policy, VisibilityTimeout and RedrivePolicy. The script will also perform an optional purge of the dead letter queue if the option is selected. Users can run the script with IsRollback and PreviousExecutionId to rollback a previous execution of this test.

## Inputs

### `MainQueueUrl`:
* type: String
* description: (Required) The URL of the main queue

### `DlqAlarmName`:
* type: String
* description: (Required) Alarm which should be red after test

### `PurgeDeadLetterQueue`:
* type: Boolean
* description: (Optional) Purge dead-letter queue and assert alarm to be green after test and also during rollback execution
* default: False

### `AutomationAssumeRole`:
* Description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf.
* Type: String

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
        * `IsRollback` it false, continue with `AssertAlarmToBeGreenBeforeStart` step
1. `PrepareRollbackOfPreviousExecution`
    * Type: aws:executeScript
    * Inputs:
        * `PreviousExecutionId`
    * Outputs:
        * `MainQueueUrl`
        * `Policy`
        * `VisibilityTimeout`
        * `RedrivePolicy`
        * `DeadLetterQueueUrl`
    * Explanation:
       * Get values of SSM Document input and output parameters from the previous execution using `PreviousExecutionId`:
         * `MainQueueUrl`
         * `BackupCurrentExecution.Policy`
         * `BackupCurrentExecution.VisibilityTimeout`
         * `BackupCurrentExecution.RedrivePolicy`
         * `BackupCurrentExecution.DeadLetterQueueUrl`
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
        * `PrepareRollbackOfPreviousExecution.VisibilityTimeout`
        * `PrepareRollbackOfPreviousExecution.RedrivePolicy`
        * `PrepareRollbackOfPreviousExecution.DeadLetterQueueUrl`
    * Explanation:
        * Set main queue attributes `Policy`, `VisibilityTimeout` and `RedrivePolicy`
1. `AssertPurgeDeadLetterQueueFlagForPreviousExecution`
   * Type: aws:branch
   * Inputs:
      * `PurgeDeadLetterQueue`
   * Default: `isEnd`
   * Outputs: none
   * Explanation:
      * If `PurgeDeadLetterQueue` input is true, continue with `PurgeDeadLetterQueueForPreviousExecution` step. If else, then stop automation.
1. `PurgeDeadLetterQueueOfPreviousExecution`
   * Type: aws:executeAutomation
   * Inputs:
      * `DocumentName`: `Digito-PurgeQueue_2021-03-11`
      * `RuntimeParameters`:
         * `AutomationAssumeRole`: {{AutomationAssumeRole}}
         * `QueueUrl`: {{PrepareRollbackOfPreviousExecution.DeadLetterQueueUrl}}
   * isEnd: true
   * Explanation:
     * Purge dead-letter queue by shared SSM Document `Digito-PurgeQueue_2021-03-11`
1. `AssertAlarmToBeGreenBeforeStart`
   * Type: aws:assertAwsResourceProperty
   * Inputs:
       * `DlqAlarmName`
       * `timeoutSeconds=10`
   * Explanation:
       * Ensure that `DlqAlarmName` alarm is `OK`
1. `BackupCurrentExecution`
    * Type: aws:executeScript
    * Inputs:
        * `MainQueueUrl`
    * Outputs:
        * `Policy`
        * `VisibilityTimeout`
        * `DeadLetterQueueUrl`
        * `DeadLetterQueueArn`
        * `RedrivePolicy`
    * Explanation:
        * Execute script to get main queue attributes `Policy`, `VisibilityTimeout` and `RedrivePolicy`
        * Get name of dead-letter queue from `deadLetterTargetArn` property in `RedrivePolicy`, then get URL of dead letter queue and set
        as `DeadLetterQueueUrl` output.
1. `UpdateQueuePolicy`
    * Type: aws:executeScript
    * Inputs:
        * `MainQueueUrl`
        * `BackupCurrentExecution.Policy`
    * Explanation:
        * Add deny rule for `sqs:DeleteMessage` action into SQS policy
    * OnFailure: step: RollbackCurrentExecution
1. `UpdateQueueAttributes`
    * Type: aws:executeAwsApi
    * Inputs:
       * `MainQueueUrl`
       * `BackupCurrentExecution.DeadLetterQueueArn`
       * `MaxReceiveCount=1`
       * `VisibilityTimeout=0`
    * Explanation:
       * Compose `RedrivePolicy` from `MaxReceiveCount=1` and `BackupCurrentExecution.DeadLetterQueueArn`
       * Set `VisibilityTimeout`, and `RedrivePolicy` attributes to the main queue
    * OnFailure: step: RollbackCurrentExecution
1. `SendMessage`
    * Type: aws:executeAwsApi
    * Inputs:
        * `MainQueueUrl`
    * Explanation:
        * Send test message to the main queue
    * OnFailure: step: RollbackCurrentExecution
1. `ReadMessage`
    * Type: aws:executeScript
    * Inputs:
        * `MainQueueUrl`
    * Explanation:
       * Read message from the main queue 2 times
    * OnFailure: step: RollbackCurrentExecution
1. `AssertAlarmToBeRed`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `DlqAlarmName`
    * Explanation:
        * Wait for `DlqAlarmName` alarm to be `ALARM` for 600 seconds
    * OnFailure: step: RollbackCurrentExecution
1. `RollbackCurrentExecution`
    * Type: aws:executeAwsApi
    * Inputs:
        * `MainQueueUrl`
        * `BackupCurrentExecution.Policy`
        * `BackupCurrentExecution.VisibilityTimeout`
        * `BackupCurrentExecution.RedrivePolicy`
    * Explanation:
        * Set main queue attributes `Policy`, `VisibilityTimeout` and `RedrivePolicy`
1. `AssertPurgeDeadLetterQueueFlag`
   * Type: aws:branch
   * Inputs:
      * `PurgeDeadLetterQueue`
   * Default: `isEnd`
   * Outputs: none
   * Explanation:
      * If `PurgeDeadLetterQueue` input is true, continue with `PurgeDeadLetterQueue` step. If else, then stop automation.
1. `PurgeDeadLetterQueue`
   * Type: aws:executeAutomation
   * Inputs:
      * `DocumentName`: `Digito-PurgeQueue_2021-03-11`
      * `RuntimeParameters`:
         * `AutomationAssumeRole`: {{AutomationAssumeRole}}
         * `QueueUrl`: {{BackupCurrentExecution.DeadLetterQueueUrl}}
   * Explanation:
      * Purge dead-letter queue by shared SSM Document `Digito-PurgeQueue_2021-03-11`
1. `AssertAlarmToBeGreen`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `DlqAlarmName`
    * Explanation:
        * Wait for `DlqAlarmName` alarm to be `OK` for 600 seconds
    * isEnd: true

## Outputs

No.