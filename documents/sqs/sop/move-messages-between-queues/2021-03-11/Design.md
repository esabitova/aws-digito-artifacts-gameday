# Id
sqs:sop:move-messages-between-queues:2021-03-11

## Intent
Moves messages from one queue to another. Can be used to restore messages from Dead Letter queue back to main operation one or visa versa.
Re-executing this document can lead to duplicate messages in the target queue if the message was not successfully transferred during the previous attempt.
Number of messages, latency (e.g. cross-region transfer) and message size can lead to a significant time for transferring messages. Since there is a hard cap of 10 minutes for executeScript action, the script would automatically stop after 9 minutes and report on how many messages have been sent so far.
Validates if given 'Source' and 'Target' queues are different types (FIFO, Standard). If so, the script will throw an error. Customers can suppress the validation by passing `ForceExecution` parameter. 
Bear in mind that in case of FIFO queue, messages might be re-ordered while being transfered to the target one. 

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
* sqs:GetQueueAttributes

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
  * default: 10
### `ForceExecution`
  * type: Boolean
  * description: (Optional) If True, validation of input parameters will be skipped
  * default: False

## Details

1.`TransferMessages`
  * Type: aws:executeScript
  * Inputs:
      * `SourceQueueUrl`
      * `TargetQueueUrl`
      * `NumberOfMessagesToTransfer`
      * `MessagesTransferBatchSize`
      * `ForceExecution`
  * Outputs:
      * `NumberOfMessagesTransferredToTarget` - the count of messages we are able to send + delete successfully
      * `NumberOfMessagesFailedToSendToTarget` - the count of messages we fail to send
      * `NumberOfMessagesFailedToDeleteFromSource` - the count of messages we sent but failed to delete
      * `TimeElapsed` - The time elapsed during the transfer
  * Explanation:
      * Determine queue types. For each of `SourceQueueUrl` and `TargetQueueUrl`:
        * Execute https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs.html#SQS.Client.get_queue_attributes 
          * Parameters:
            * `QueueUrl`=`QueueUrl`
            * `AttributeNames`=`All`
          * if `FifoQueue` exists then it is a FIFO Queue, otherwise it is a Standard one
          * if `ForceExecution` is not set: 
            * Compare the queue type of source and target queues and throw an error saying that the types of the given queues are different
          * if `ForceExecution`, skip the validation and continue with normal execution
      * In a loop while number of messages transferred less than `NumberOfMessagesToTransfer` or time elapsed less than 9 minutes 
        1. Receive messages by executing https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs.html#SQS.Client.receive_message 
          * Parameters:
            * `QueueUrl`=`SourceQueueUrl`
            * `MaxNumberOfMessages`=`MessagesTransferBatchSize`
          * Get received message handlers.
        2. Send messages to the target queue using https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs.html#SQS.Client.send_message_batch 
          * Parameters:
            * `QueueUrl`=`TargetQueueUrl`
            * `Entries`=[`the messages taken from the step #1`]. There are 4 specific cases depending on target and source queue types that should be handled when passing messages:
              * Standard -> FIFO: Generate `MessageDeduplicationId` as Guid (uuid) and `MessageGroupId` as Guid (uuid) for the each of the received entries
              * FIFO -> Standard: Cleanup `MessageDeduplicationId` and `MessageGroupId` for each of the received entries
              * Standard -> Standard: send messages as they are
              * FIFO -> FIFO: send messages as they are
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
