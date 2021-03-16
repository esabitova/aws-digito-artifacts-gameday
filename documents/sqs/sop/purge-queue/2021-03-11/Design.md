# Id
sqs:sop:purge-queue:2021-03-11

## Intent
Cleans up given queue


## Type
Software Outage SOP

## Risk
High

## Requirements
* SQS Queue

## Permission required for AutomationAssumeRole (TBD)
* some policy

## Supports Rollback
No.

## Inputs (TBD)
### `AutomationAssumeRole`
  * type: String
  * description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf
### `QueueArn`
  * type: String
  * description: (Required) The ARN of the SQS Queue

## Details

1.`Apply`
  * Type: aws:executeAwsApi
  * Inputs:
      * `QueueArn`
  * Outputs: none
  * Explanation:
      * https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs.html#SQS.Client.purge_queue

## Outputs
None
