# Id
sqs:test:queue_redrive_standard:2020-11-27

## Intent
Test standard SQS behavior after receiving a message maximum allowed times

## Type
Software Outage Test

## Risk
High

## Requirements
* Existing standard main queue with enabled dead-letter queue feature
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
* sqs:DeleteMessage
* ssm:StartAutomationExecution 
* ssm:GetAutomationExecution
* iam:PassRole

## Supports Rollback

Yes. The script will perform rollback of main queue attributes: Policy, VisibilityTimeout and RedrivePolicy. Then will delete test message from the dead-letter queue, and  move all messages from the dead-letter to the main queue. Users can run the script with IsRollback and PreviousExecutionId.

## Inputs

### `MainQueueUrl`:
* type: String
* description: (Required) The URL of the main queue

### `DlqAlarmName`:
* type: String
* description: (Required) Alarm which should be red after test
 
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
        * `IsRollback` is true, continue with `PrepareRollbackOfPreviousExecution` step
        * `IsRollback` is false, continue with `AssertAlarmToBeGreenBeforeStart` step
1. `PrepareRollbackOfPreviousExecution`
    * Type: aws:executeScript
    * Inputs:
        * `PreviousExecutionId`
    * Outputs:
        * `MainQueueUrl`
        * `DeadLetterQueueUrl`  
        * `Policy`
        * `VisibilityTimeout`
        * `RedrivePolicy`
        * `MessageID`
    * Explanation:
       * Get values of SSM Document input and output parameters from the previous execution using `PreviousExecutionId`:
         * `MainQueueUrl`
         * `BackupCurrentExecution.DeadLetterQueueUrl`
         * `BackupCurrentExecution.Policy`
         * `BackupCurrentExecution.VisibilityTimeout`
         * `BackupCurrentExecution.RedrivePolicy`
         * `SendMessage.MessageID`
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
    * Explanation:
        * Set main queue attributes `Policy`, `VisibilityTimeout` and `RedrivePolicy`
1. `MoveMessagesForPreviousExecution`
   * Type: aws:executeAutomation
   * Inputs:
      * `DocumentName`: `Digito-MoveSQSMessagesBetweenQueuesSOP_2021-03-11`
      * `RuntimeParameters`:
         * `AutomationAssumeRole`: {{AutomationAssumeRole}}
         * `MainQueueUrl`: {{PrepareRollbackOfPreviousExecution.MainQueueUrl}}
         * `DeadLetterQueueUrl`: {{PrepareRollbackOfPreviousExecution.DeadLetterQueueUrl}}
   * Explanation:
      * Move all messages from dead-letter to the main queue by shared SSM Document `Digito-MoveSQSMessagesBetweenQueuesSOP_2021-03-11`
1. `DeleteMessageForPreviousExecution`
   * Type: aws:executeScript
   * Inputs:
      * `PrepareRollbackOfPreviousExecution.DeadLetterQueueUrl`
      * `PrepareRollbackOfPreviousExecution.MessageID`
   * isEnd: true   
   * Explanation:
      * Delete the test message with specified MessageID from the dead-letter queue
1. `AssertAlarmToBeGreenBeforeStart`
   * Type: aws:waitForAwsResourceProperty
   * Inputs:
       * `DlqAlarmName`
   * Explanation:
       * Ensure that `DlqAlarmName` alarm is `OK` for 600 seconds
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
    * Outputs:
        * `MessageID`
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
1. `RollbackCurrentExecutionQueuePolicy`
    * Type: aws:executeAwsApi
    * Inputs:
        * `MainQueueUrl`
        * `BackupCurrentExecution.Policy`
        * `BackupCurrentExecution.VisibilityTimeout`
        * `BackupCurrentExecution.RedrivePolicy`
    * Explanation:
       * Set main queue attributes `Policy`, `VisibilityTimeout` and `RedrivePolicy`
1. `DeleteMessage`   
   * Type: aws:executeScript
   * Inputs:
        * `BackupCurrentExecution.DeadLetterQueueUrl`
        * `SendMessage.MessageID`
   * Explanation:
        * Delete the test message with specified MessageID from the dead-letter queue
   * OnFailure: step: RollbackCurrentExecution
1. `MoveMessages`
   * Type: aws:executeAutomation
   * Inputs:
      * `DocumentName`: `Digito-MoveSQSMessagesBetweenQueuesSOP_2021-03-11`
      * `RuntimeParameters`:
         * `AutomationAssumeRole`: {{AutomationAssumeRole}}
         * `TargetQueueUrl`: {{MainQueueUrl}}
         * `SourceQueueUrl`: {{BackupCurrentExecution.DeadLetterQueueUrl}}
   * Explanation:
      * Move all messages from dead-letter to the main queue by shared SSM Document `Digito-MoveSQSMessagesBetweenQueuesSOP_2021-03-11`
1. `AssertAlarmToBeGreen`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `DlqAlarmName`
    * Explanation:
        * Wait for `DlqAlarmName` alarm to be `OK` for 600 seconds
    * isEnd: true

## Outputs

No.

