# Id

dynamodb:sop:update_provisioned_capacity:2020-04-01

## Intent

Used to Update provisioned capacity for DynamoDB Table

## Type

Software Outage SOP

## Risk

Small

## Requirements

* A DynamoDB table

## Permission required for AutomationAssumeRole

* dynamodb:UpdateTable
* dynamodb:DescribeTable

## Supports Rollback

No.

## Inputs

### `DynamoDBTableName`

* Description: (Required) The DynamoDB Table Name.
* Type: String

### `DynamoDBTableRCU`

* Description: (Required) The DynamoDB Table Read Capacity Units.
* Type: Integer

### `DynamoDBTableWCU`

* Description: (Required) The DynamoDB Table Write Capacity Units.
* Type: Integer

### AutomationAssumeRole:

* Description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf.
* Type: String

## Details of SSM Document steps:

1. `UpdateDynamoDBTableProvisionedCapacity`
    * Type: aws:executeScript
    * Inputs:
        * `DynamoDBTableName`
        * `DynamoDBTableRCU`
        * `DynamoDBTableWCU`
    * Outputs:
        * `UpdateStartTime`: used to calculate the duration of update
    * Explanation:
        * Update the dynamodb table ProvisionedThroughput values.  [update_table](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_UpdateTable.html) method
1. `VerifyDynamoDBTableUpdateStatus`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `Service`
        * `Api`
        * `TableName`: `DynamoDBTableName`
        * `PropertySelector`
        * `DesiredValues`
    * Explanation:
        * Describe the dynamodb table to get the information about the current status of the
          table. [describe_table](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_DescribeTable.html) method
1. `CalculateUpdateDuration`
   * Type: aws:executeScript
   * Inputs:
      * `UpdateDynamoDBTableProvisionedCapacity.UpdateStartTime`
   * Outputs:
      * `UpdateDuration`: the duration of the provisioned capacity update
   * Explanation:
      * Get the difference between now and UpdateDynamoDBTableProvisionedCapacity.UpdateStartTime
1. `GetUpdatedProvisionedThroughput`
    * Type: aws:executeAwsApi
    * Inputs:
        * `Service`
        * `Api`
        * `TableName`
    * Outputs:
        * `ReadCapacityUnits` : The Updated Read Capacity Units
        * `WriteCapacityUnits`: The Updated Write Capacity Units
    * Explanation:
        * Describe the dynamodb table to get the information about the ProvisionedThroughput of the
          table.  [describe_table](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_DescribeTable.html) method

## Outputs

* `GetUpdatedProvisionedThroughput.ReadCapacityUnits` : The DynamoDB Table new ReadCapacityUnits
* `GetUpdatedProvisionedThroughput.WriteCapacityUnits`: The DynamoDB Table new WriteCapacityUnits
* `CalculateUpdateDuration.UpdateDuration`: the duration of the provisioned capacity update
 

