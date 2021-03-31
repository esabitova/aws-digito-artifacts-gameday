# Id

sqs:test:capacity_failure:2021-03-13

## Intent

Test SQS behaviour after sending a message bigger than threshold for SentMessageSizeMaximum alarm 

## Type

Software Outage Test

## Risk

Medium

## Requirements

* Existing queue 
* Existing alarm for SentMessageSize metric on the queue

## Permission required for AutomationAssumeRole

* cloudwatch:DescribeAlarms
* sqs:SendMessage
* sqs:ReceiveMessage
* sqs:DeleteMessage
* ssm:GetAutomationExecution
* ssm:GetParameters

## Supports Rollback

Yes. The script removes test message from the queue. Users can run the script with IsRollback and PreviousExecutionId to remove message sent by previous execution

## Inputs

### `QueueUrl`

* description: (Required) The URL of the queue
* type: String

### `SentMessageSizeAlarmName`

* type: String
* description: (Required) Alarm which should be red after injection of the failure and green after the rollback process in the end of the test.

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
      * if `IsRollback` is true, continue with `PrepareRemoveOfFailureMessage` step
      * if `IsRollback` is false, continue with `AssertAlarmToBeGreenBeforeTest` step
1. `PrepareRemoveOfFailureMessage`
   * Type: aws:executeScript
   * Inputs:
      * `PreviousExecutionId`
   * Outputs:
      * `MessageId`: The message ID to delete
   * Explanation:
       * Get values of SSM Document output parameters from the previous execution using `PreviousExecutionId`:
           * `MessageId` from step `SendCapacityFailureMessage`
1. `RemovePreviousExecutionFailureMessage`
   * Type: aws:executeScript
   * Inputs:
      * `PrepareRemoveOfFailureMessage.MessageId`
      * `Timeout`: Maximum time in seconds to poll queue for messages
   * Explanation:
      * Poll queue using [receive_message](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs.html#SQS.Client.receive_message)
        from `sqs` service and loop through messages until the message with ID `MessageId` is found
      * Get `ReceiptHandle` from message
      * Use [delete_message](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs.html#SQS.Client.delete_message)
      from `sqs` service to delete the message by its `ReceiptHandle`
      * Throw exception if message not found before `TimeOut`

1. `AssertAlarmToBeGreenBeforeTest`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `AlarmNames`: Name of the alarm with SentMessageSize metric (`SentMessageSizeAlarmName`)
    * Outputs: none
    * Explanation:
        * Wait for 600 seconds for the alarm to be in `OK` state
1. `GetAlarmThreshold`
    * Type: aws:executeScript
        * Inputs:
            * `AlarmName`: The name of the alarm with size threshold (`SentMessageSizeAlarmName`)
        * Outputs:
            * `SizeAboveThreshold`: Value slightly higher than the threshold
        * Explanation:
            * Use [describe_alarms](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudwatch.html#CloudWatch.Client.describe_alarms)
            from `cloudwatch` service to get `Threshold` of the alarm by `AlarmName`
            * Return value above the threshold

1. `SendCapacityFailureMessage`
   * Type: aws:executeAwsApi
   * Inputs:
      * `InputPayload`:
         * `QueueUrl`: The URL of the queue (`QueueUrl`)
         * `MessageSize`: Size of the message in bytes above alarm's threshold (`GetAlarmThreshold.SizeAboveThreshold`)
         * `MessageDeduplicationId`: Unique token in case of FIFO queues (`{{global:DATE_TIME}}`)
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
        * Wait 300 seconds for the alarm to be in `ALARM` state
    * OnFailure: step: RollbackCurrentExecution
1. `RollbackCurrentExecution`
   * Type: aws:executeScript
   * Inputs:
      * `SendCapacityFailureMessage.MessageId`
      * `Timeout`: Maximum time in seconds to poll queue for messages
   * Explanation:
      * Poll queue using [receive_message](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs.html#SQS.Client.receive_message)
        from `sqs` service and loop through messages until the message with ID `MessageId` is found
      * Get `ReceiptHandle` from message
      * Use [delete_message](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs.html#SQS.Client.delete_message)
      from `sqs` service to delete the message by its `ReceiptHandle`
      * Throw exception if message not found before `TimeOut`
1. `AssertAlarmToBeGreen`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `AlarmNames`: Name of the alarm with SentMessageSize metric (`SentMessageSizeAlarmName`)
    * Outputs: none
    * Explanation:
        * Wait for 600 seconds for the alarm to be in `OK` state
## Outputs

No.
	 