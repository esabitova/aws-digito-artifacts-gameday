# Id
sqs:sop:move-messages-between-queues:2021-03-11

## Intent
Moves messages from one queue to another. Can be used to restore messages from Dead Letter queue back to main operation one or visa versa


## Type
Software Outage SOP

## Risk
Medium

## Requirements
* Source SQS Queue
* Target SQS Queue

## Permission required for AutomationAssumeRole (TBD)
* some policy

## Supports Rollback
No.

## Inputs (TBD)
### `AutomationAssumeRole`
  * type: String
  * description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf
### `SourceQueueArn`
  * type: String
  * description: (Required) The ARN of the SQS Queue
### `TargetQueueArn`
  * type: Integer
  * description: (Required) The ARN of the SQS Queue
### `NumberOfMessagesToTransfer`
  * type: Integer
  * description: (Required) The ARN of the SQS Queue

## Details

1.`Apply`
  * Type: aws:executeScript
  * Inputs:
      * `SourceQueueArn`
      * `TargetQueueArn`
      * `NumberOfMessagesToTransfer`
  * Outputs:
      * `NumberOfMessagesTransfered`
  * Explanation:
      * receive and send continious while queue isn't empty or reach `NumberOfMessagesToTransfer`
      * Use batches when transfing messages
      * Note: millions of messages + latency (e.g. cross-region transfer) + message size can lead to a significant time of execution of the current SOP. Hard cap for task execution is 10 minuts (see https://docs.aws.amazon.com/general/latest/gr/ssm.html)

## Outputs
* `Apply.NumberOfMessagesTransfered` 
