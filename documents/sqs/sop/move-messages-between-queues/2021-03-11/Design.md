# Id
sqs:sop:move-messages-between-queues:2021-03-11

## Intent
Move messages from one queue to another. Can be used to restore messages from Dead Letter queue back to main operation one or visa versa.
Re-executing this document can lead to duplicate messages in the target queue if the message was not successfully transferred during the previous attempt.
Number of messages, latency (e.g. cross-region transfer) and message size can lead to a significant time for transferring messages. Since there is a hard cap of 10 minutes for executeScript action, the script would automatically stop after 9 minutes and report on how many messages have been sent so far.
Bear in mind that in case of FIFO queue, messages might be re-ordered while being transferred to the target one. 

## Type
Software Outage SOP

## Risk
Medium

## Requirements
* Source SQS Queue
* Target SQS Queue

## Permission required for AutomationAssumeRole
* sqs:SendMessageBatch
* sqs:DeleteMessageBatch
* sqs:ReceiveMessage

## Supports Rollback
No.

## Inputs
### `AutomationAssumeRole`
  * type: String
  * description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf.
### `SourceQueueUrl`
  * type: String
  * description: (Required) The URL of the source SQS Queue.
### `TargetQueueUrl`
  * type: Integer
  * description: (Required) The URL of the target SQS Queue.
### `NumberOfMessagesToTransfer`
  * type: Integer
  * description: (Required) The number of messages to be sent.
### `MessagesTransferBatchSize`
  * type: Integer
  * description: (Optional) The number of messages that going to be transferred per batch. Maximum is 10
  * default: 1

## Details

1.`TransferMessages`
  * Type: aws:executeScript
  * Inputs:
      * `SourceQueueUrl`
      * `TargetQueueUrl`
      * `NumberOfMessagesToTransfer`
      * `MessagesTransferBatchSize`
  * Outputs:
      * `NumberOfMessagesTransferredToTarget` - the count of messages we are able to send + delete successfully
      * `NumberOfMessagesFailedToSendToTarget` - the count of messages we fail to send
      * `NumberOfMessagesFailedToDeleteFromSource` - the count of messages we sent but failed to delete
      * `TimeElapsed` - The time elapsed during the transfer
  * Explanation:
      * In a loop while number of messages transferred less than `NumberOfMessagesToTransfer` or time elapsed less than 9 minutes 
        1. Receive messages by executing https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs.html#SQS.Client.receive_message 
          * Parameters:
            * `QueueUrl`=`SourceQueueUrl`
            * `MaxNumberOfMessages`=`MessagesTransferBatchSize`
          * Get received message handlers.
        2. Send messages to the target queue using https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs.html#SQS.Client.send_message_batch 
          * Parameters:
            * `QueueUrl`=`TargetQueueUrl`
            * `Entries`=[`the messages taken from the step #1`]
          * Parse output, take failed messages and increment `NumberOfMessagesFailedToSendToTarget`. Take successfully sent message Ids and derive a list by joining with Received Messages, also increment `NumberOfMessagesTransferredToTarget`
        3. Delete messages from the source queue using https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs.html#SQS.Client.delete_message_batch
          * Parameters
            * `QueueUrl`=`SourceQueueUrl`
            * `Entries`=[`The messages that were successfully sent to the target queue (successful result of step #2 and #1)`]
          * Parse output, calculate failed messages and increment `NumberOfMessagesFailedToDeleteFromSource`

## Outputs
* `TransferMessages.NumberOfMessagesTransferredToTarget` 
* `TransferMessages.NumberOfMessagesFailedToSendToTarget` 
* `TransferMessages.NumberOfMessagesFailedToDeleteFromSource` 
* `TransferMessages.TimeElapsed` 
