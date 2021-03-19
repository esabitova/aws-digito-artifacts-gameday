# Id
sqs:sop:purge-queue:2021-03-11

## Intent
Cleans up the given queue


## Type
Software Outage SOP

## Risk
High

## Requirements
* SQS Queue

## Permission required for AutomationAssumeRole
* sqs:PurgeQueue

## Supports Rollback
No.

## Inputs
### `AutomationAssumeRole`
  * type: String
  * description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf
### `QueueUrl`
  * type: String
  * description: (Required) The URL of the SQS Queue

## Details
1.`PurgeQueue`
  * Type: aws:executeAwsApi
  * Inputs:
      * `QueueUrl`
  * Outputs: none
  * Explanation:
      * Execute https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs.html#SQS.Client.purge_queue with the following parameters:
        * `QueueUrl`=`QueueUrl`

## Outputs
None
