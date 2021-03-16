# Id

sqs:test:capacity_failure_standard:2021-03-13

## Intent

Test SQS behaviour after sending a message bigger than allowed size by a customer (SentMessageSizeMaximum) or 256 KB -30% (185KB) to standard queue

## Type

Software Outage Test

## Risk

Low

## Requirements

* Existing standard queue 
* Existing alarm for SentMessageSize metric on the queue

## Permission required for AutomationAssumeRole

* cloudwatch:DescribeAlarms
* sqs:SendMessage
* sqs:ReceiveMessage
* sqs:DeleteMessage
* ssm:GetParameters
* ssm:StartAutomationExecution
* ssm:GetAutomationExecution
* iam:PassRole

## Supports Rollback

Yes. The script removes test message from the queue. Users can run the script with IsRollback and PreviousExecutionId to remove message sent by previous execution

## Inputs

### `QueueUrl`

* description: (Required) The URL of the queue
* type: String

### `SentMessageSizeAlarmName`

* type: String
* description: (Optional) Alarm which should be red after injection of the failure and green after the rollback process in the end of the test.
* default: 'SentMessageSizeAlarm'

### `SentMessageSizeMaximum`

* type: Number
* description: (Optional) Requested size of the message higher than threshold (defaults to 256KB-30%) 
* default: 185000 (bytes)

### `AlarmWaitTimeout`

* type: Integer
* description: (Required) Alarm wait timeout
* default: 300 (seconds)

### `IsRollback`:

* type: Boolean
* description: (Optional) Run rollback step of the given previous execution (parameter `PreviousExecutionId`)
* default: False

### `PreviousExecutionId`:

* type: String
* description: (Optional) The id of previous execution of the current script
* default: ''

## Details of SSM Document steps:

1. `CheckIsRollback`
   * Type: aws:branch
   * Inputs:
      * `IsRollback`
   * Outputs: none
   * Explanation:
      * if `IsRollback` is true, continue with `PrepareRollbackOfPreviousExecution` step
      * if `IsRollback` is false, continue with `SendCapacityFailureMessage` step
1. `PrepareRollbackOfPreviousExecution`
   * Type: aws:executeScript
   * Inputs:
      * `PreviousExecutionId`
   * Outputs:
      * `MessageId`: The message ID to delete
   * Explanation:
      * Get values of SSM Document input parameters from the previous execution using `PreviousExecutionId`:
         * `MessageId` from step `SendCapacityFailureMessage`
1. `RollbackPreviousExecution`
   * Type: aws:executeAutomation
   * Inputs:
      * `PrepareRollbackOfPreviousExecution.MessageId`
      * `Timeout`: Maximum time in seconds to poll queue for messages
   * Explanation:
      * Poll queue using [receive_message](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs.html#SQS.Client.receive_message)
        from `sqs` service and loop from messages until the message with ID `MessageID` is found
      * Get `ReceiptHandle` from message
      * Use [delete_message](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs.html#SQS.Client.delete_message)
      from `sqs` service to delete the message by its `ReceiptHandle`
      * Throw exception if message not found before `TimeOut`

1. `SendCapacityFailureMessage`
   * Type: aws:executeAwsApi
   * Inputs:
      * `InputPayload`:
         * `QueueUrl`: The URL of the queue (`QueueUrl`)
         * `MessageSize`: Size of the message in bytes (`SentMessageSizeMaximum`)
   * Outputs:
      * `MessageId`: Id of the sent message
   * Explanation:
      * Use [send_message](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs.html#SQS.Client.send_message)
      from `sqs` service to send message to queue with content body of size `MessageSize` in bytes
1. `AssertAlarmToBeRed`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `AlarmNames`: Name of the alarm with SentMessageSize metric (`SentMessageSizeAlarmName`)
    * Outputs: none
    * Explanation:
        * Wait `AlarmWaitTimeout` seconds for the alarm to be in `ALARM` state
    * OnFailure: step: RollbackCurrentExecution
1. `RollbackCurrentExecution`
   * Type: aws:executeAutomation
   * Inputs:
      * `SendCapacityFailureMessage.MessageId`
      * `Timeout`: Maximum time in seconds to poll queue for messages
   * Explanation:
      * Poll queue using [receive_message](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs.html#SQS.Client.receive_message)
        from `sqs` service and loop from messages until the message with ID `MessageID` is found
      * Get `ReceiptHandle` from message
      * Use [delete_message](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs.html#SQS.Client.delete_message)
      from `sqs` service to delete the message by its `ReceiptHandle`
      * Throw exception if message not found before `TimeOut`
1. `SendNormalMessage`
   * Type: aws:executeAwsApi
   * Inputs:
      * `InputPayload`:
         * `QueueUrl`: The URL of the queue (`QueueUrl`)
         * `MessageSize`: Size of the message in bytes (small value)
   * Outputs:
      * `MessageId`: Id of the sent message
   * Explanation:
      * Use [send_message](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs.html#SQS.Client.send_message)
      from `sqs` service to send a message to queue with content body of size `MessageSize` in bytes
1. `AssertAlarmToBeGreen`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `AlarmNames`: Name of the alarm with SentMessageSize metric (`SentMessageSizeAlarmName`)
    * Outputs: none
    * Explanation:
        * Wait `AlarmWaitTimeout` seconds for the alarm to be in `OK` state
1. `DeleteNormalMessage`
   * Type: aws:executeAutomation
   * Inputs:
      * `SendCapacityFailureMessage.MessageId`
      * `Timeout`: Maximum time in seconds to poll queue for messages
   * Explanation:
      * Poll queue using [receive_message](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs.html#SQS.Client.receive_message)
        from `sqs` service and loop from messages until the message with ID `MessageID` is found
      * Get `ReceiptHandle` from message
      * Use [delete_message](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs.html#SQS.Client.delete_message)
      from `sqs` service to delete the message by its `ReceiptHandle`
      * Throw exception if message not found before `TimeOut`
## Outputs

No.
	 