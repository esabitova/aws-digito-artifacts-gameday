# Id
dynamodb:util:copy_table_properties:2020-04-01

## Document Type
Automation

## Inputs
### `DynamoDBTableSourceName`
    * type: String
    * description: (Required) The DynamoDB Table Source Name.
### `DynamoDBTableTargetName`
    * type: String
    * description: (Required) The DynamoDB Table Target Name.
### `DynamoDBSourceTableAlarmNames`
    * type: StringList
    * description: (Optional) The DynamoDB Source Table Name Alarm Names.
### `AutomationAssumeRole`
    * type: String
    * description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf.

## Outputs
None
