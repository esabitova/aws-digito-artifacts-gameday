# Id
dynamodb:sop:restore_from_backup:2020-04-01

## Intent
Used to recover the table into a known good state by existing backup of DynamoDB table

## Type
Software Outage SOP

## Risk
Small

## Requirements
* A DynamoDB table
* The Dynamodb table backup

## Notes

The following properties can't be restored by the backup :
* Triggers
* Item count doesn't appear immediately because dynamodb update this value each 6 hours.
* IAM policy

## Permission required for AutomationAssumeRole
* dynamodb:RestoreTableFromBackup
* dynamodb:DescribeTable
* dynamodb:Scan
* dynamodb:Query
* dynamodb:UpdateItem
* dynamodb:PutItem
* dynamodb:GetItem
* dynamodb:DeleteItem
* dynamodb:BatchWriteItem
* dynamodb:UpdateContinuousBackups
* dynamodb:UpdateTable
* dynamodb:DescribeKinesisStreamingDestination
* dynamodb:EnableKinesisStreamingDestination
* dynamodb:DescribeTimeToLive
* dynamodb:UpdateTimeToLive
* dynamodb:ListTagsOfResource
* dynamodb:TagResource
* dynamodb:DescribeContributorInsights
* dynamodb:UpdateContributorInsights
* dynamodb:DescribeContinuousBackups
* dynamodb:UpdateContinuousBackups
* dynamodb:DescribeGlobalTable
* dynamodb:CreateGlobalTable
* application-autoscaling:RegisterScalableTarget
* application-autoscaling:DescribeScalableTargets
* cloudwatch:DescribeAlarms
* cloudwatch:PutMetricAlarm
* iam:passRole

## Supports Rollback
No.

## Inputs

### DynamoDBSourceTableName

* Description: (Required) The DynamoDB Source Table Name.
* Type: String

### DynamoDBSourceGlobalTableName

* Description: (Optional) The DynamoDB Source Global Table Name.
* Type: String
* Default: 'None'

### DynamoDBSourceTableIndexName

* Description: (Optional) The DynamoDB Source Index Name.
* Type: String
* Default: 'None'

### DynamoDBTargetTableIndexName

* Description: (Optional) The DynamoDB Target Index Name.
* Type: String
* Default: 'None'

### DynamoDBTargetGlobalTableName

* Description: (Optional) The DynamoDB Target Global Table Name.
* Type: String
* Default: 'None'

### DynamoDBSourceTableAlarmNames

* Description: (Optional) The DynamoDB Source Table Name Alarm Names.
* Type: ListString
* default: ['']

### DynamoDBSourceTableBackupArn

* Description: (Required) The DynamoDB Source Table Backup ARN.
* Type: String

### DynamoDBTargetTableName

* Description: (Required) The DynamoDB Target Table Name.
* Type: String

### AppASGDynamoDBIamRole

* Description: (Required) An IAM role to be assumed by the application autoscaling group and which allow it to dynamodb target table scaling properties.
* Type: String

### AutomationAssumeRole:

* Description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf.
* Type: String

## Details of SSM Document steps:

1. `RecordStartTime`
    * Type: aws:executeScript
    * Inputs:
    * Outputs:
        * `StartExecutionTime`: The timestamp when the step execution started
    * Explanation:
        * Calculate the time when the dynamodb table recovery starts

1. `RestoreDynamoDBTableFromBackup`
    * Type: aws:executeAwsApi
    * Inputs:
        * `TargetTableName`: pass DynamoDBTargetTableName parameter
        * `BackupArn`: pass DynamoDBSourceTableBackupArn parameter
    * Outputs:
        * `TargetTableArn`: The ARN of the target table restored from the backup
        * `RecoveryPoint`: The recovery point objective: RestoreDateTime value
    * Explanation:
        * Restore the source table backup to a new table by passing respectively the `DynamoDBTargetTableName` and `DynamoDBSourceTableBackupArn` parameters to the `TargetTableName` and `BackupArn` properties of the dynamodb `RestoreTableFromBackup` API Call. [restore_table_from_backup](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html#DynamoDB.Client.restore_table_from_backup) method

1. `VerifyDynamoDBTableTargetStatusAfterRestoreTableFromBackup`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `Service`: dynamodb
        * `Api`: DescribeTable
        * `TableName`: pass DynamoDBTargetTableName parameter
        * `PropertySelector`: use the $.Table.TableStatus selector
        * `DesiredValues`: needs to be in ACTIVE status
    * Explanation:
        * Wait for the restored table to be in ACTIVE status after the restore from backup operation is completed. [describe_table](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_DescribeTable.html) method
        * Use the shared SSM Document as the step to avoid duplicates.

1. `GetSourceDynamoDBTableStream`
    * Type: aws:executeAwsApi
    * Inputs:
        * `Service`: dynamodb
        * `Api`: DescribeTable
        * `TableName`: pass DynamoDBSourceTableName parameter
    * Outputs:
        * `SourceTableStreamEnabled`: The dynamoDB source table stream status value, true or false, from the `StreamSpecification` property
        * `SourceTableStreamViewType`: The type of the stream view value for the source dynamodb table, KEYS_ONLY, NEW_IMAGE, OLD_IMAGE or NEW_AND_OLD_IMAGES, from the `StreamSpecification` property
    * Explanation:
        * Get the source dynamodb table stream properties as they are not restored by the backup. [describe_table](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_DescribeTable.html) method

1. `CheckSourceDynamoDBTableStreamStatus`
    * Type: aws:branch
    * Inputs:
        * `SourceTableStreamEnabled`: The dynamoDB source table stream status value from the previous step.
    * Outputs: none
    * Default: Go to the step `GetSourceDynamoDBTableKinesisStreamDestination`
    * Explanation:
        * If `SourceTableStreamEnabled` is true, go to the step `UpdateTargetDynamoDBTableStream`. Otherwise, it will go to the default step.

1. `UpdateTargetDynamoDBTableStream`
    * Type: aws:executeAwsApi
    * Inputs:
        * `Service`: dynamodb
        * `Api`: UpdateTable
        * `TableName`: pass DynamoDBTargetTableName parameter
        * `StreamSpecification`: pass the `SourceTableStreamEnabled` and `SourceTableStreamViewType` values from the previous step
    * Outputs:
        * `TargetTableStreamEnabled`: The dynamoDB target table stream status value, true or false, from the `StreamSpecification` property
        * `TargetTableStreamViewType`: The type of the stream view value for the target dynamodb table, KEYS_ONLY, NEW_IMAGE, OLD_IMAGE or NEW_AND_OLD_IMAGES, from the `StreamSpecification` property
    * Explanation:
        * Restore the target dynamodb table stream properties from the source dynamodb table. [update_table](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_UpdateTable.html) method

1. `VerifyDynamoDBTableTargetStatusAfterUpdateTargetDynamoDBTableStream`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `Service`: dynamodb
        * `Api`: DescribeTable
        * `TableName`: pass DynamoDBTargetTableName parameter
        * `PropertySelector`: use the $.Table.TableStatus selector
        * `DesiredValues`: needs to be in ACTIVE status
    * Explanation:
        * Wait for the restored table to be in ACTIVE status. [describe_table](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_DescribeTable.html) method
        * Use the shared SSM Document as the step to avoid duplicates

1. `GetSourceDynamoDBTableKinesisStreamDestination`
    * Type: aws:executeScript
    * Inputs:
        * `TableName`: pass DynamoDBSourceTableName parameter
    * Outputs:
        * `SourceTableKinesisStreamArns`: The list of dynamodb source table kinesis stream ARN from the `KinesisDataStreamDestinations` property
        * `SourceTableKinesisStreamDestinationStatus`: The source dynamodb table kinesis destination stream status from the `KinesisDataStreamDestinations` property, the value will be ACTIVE if at least one `DestinationStatus` is ACTIVE
    * Explanation:
        * Get the list of source dynamodb table kinesis streaming ARNs, and the destination status as they are not restored by the backup. [describe_kinesis_streaming_destination](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html#DynamoDB.Client.describe_kinesis_streaming_destination) method

1. `CheckSourceDynamoDBTableKinesisStreamDestinationStatus`
    * Type: aws:branch
    * Inputs:
        * `SourceTableKinesisStreamDestinationStatus`: The dynamodb source table kinesis stream status from the previous step
    * Outputs: none
    * Default: Go to the step `GetSourceDynamoDBTableTimeToLive`
    * Explanation:
        * If `SourceTableKinesisStreamDestinationStatus` is ACTIVE, go to the step `EnableTargetDynamoDBTableKinesisStreamDestination`. Otherwise, it will go to the default step

1. `EnableTargetDynamoDBTableKinesisStreamDestination`
    * Type: aws:executeScript
    * Inputs:
        * `TableName`: pass DynamoDBTargetTableName parameter
        * `StreamArns`: pass `SourceTableKinesisStreamArns` value from the `GetSourceDynamoDBTableKinesisStreamDestination` step
    * Outputs:
        * `TargetTableDestinationStatus`: The dynamoDB target table kinesis stream destination status, the value will be ACTIVE if at least one `DestinationStatus` is ACTIVE
    * Explanation:
        * Add kinesis stream ARN to the target dynamodb table destination stream when enabled. `[enable_kinesis_streaming_destination](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html#DynamoDB.Client.enable_kinesis_streaming_destination) method

1. `GetSourceDynamoDBTableTimeToLive`
    * Type: aws:executeAwsApi
    * Inputs:
        * `Service`: dynamodb
        * `Api`: DescribeTimeToLive
        * `TableName`: pass DynamoDBSourceTableName parameter
    * Outputs:
        * `SourceTableTimeToLiveStatus`: The dynamoDB source table time to live status value from the `TimeToLiveDescription` property
        * `SourceTableAttributeName`: The dynamoDB source table attribute name value from the `TimeToLiveDescription` property
    * Explanation:
        * Get the time to live attribute name and status from the source dynamodb table as they are not restored by the backup. [describe_time_to_live](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_DescribeTimeToLive.html) method

1. `CheckSourceDynamoDBTableTimeToLive`
    * Type: aws:branch
    * Inputs:
        * `SourceTableTimeToLiveStatus`: The dynamoDB source table time to live status value from the previous step.
    * Outputs: none
    * Default: Go to the step `GetSourceDynamoDBTableTags`
    * Explanation:
        * If `SourceTableTimeToLiveStatus` is ENABLED, go to the step `UpdateTargetDynamoDBTableTimeToLive`. Otherwise, it will go to the default step.

1. `UpdateTargetDynamoDBTableTimeToLive`
    * Type: aws:executeAwsApi
    * Inputs:
        * `Service`: dynamodb
        * `Api`: UpdateTimeToLive
        * `TableName`: pass DynamoDBSourceTableName parameter
        * `TimeToLiveSpecification`: pass the `SourceTableTimeToLiveStatus` and `SourceTableAttributeName` values from the previous step
    * Outputs:
        * `TargetTableTimeToLiveEnabled`: The dynamoDB target table time to live status value from the `TimeToLiveSpecification` property
    * Explanation:
        * Update the time to live attribute name and status for the target dynamodb table.
          [update_time_to_live](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_UpdateTimeToLive.html) method

1. `GetSourceDynamoDBTableTags`
    * Type: aws:executeScript
    * Inputs:
        * `SourceTableArn`: pass `arn:aws:dynamodb:{{ global:REGION }}:{{ global:ACCOUNT_ID }}:table/{{ DynamoDBSourceTableName }}`
    * Outputs:
        * `SourceTableTagsStatus`: The dynamoDB source table tags status : EMPTY or NOT_EMPTY
        * `SourceTableTags`: The dynamoDB source table list of key value tags
    * Explanation:
        * Check if the dynamodb source table contains or not tags. [list_tags_of_resource](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html#DynamoDB.Client.list_tags_of_resource) method

1. `CheckSourceDynamoDBTableTags`
    * Type: aws:branch
    * Inputs:
        * `SourceTableTagsStatus`: The dynamoDB source table tags status from the previous step
    * Outputs: none
    * Default: Go to the step `GetSourceDynamoDBTableContributorInsights`
    * Explanation:
        * If `SourceTableTagsStatus` is not empty, go to the step `UpdateTargetDynamoDBTableTags`. Otherwise, the restored dynamodb target table won't have tags.

1. `UpdateTargetDynamoDBTableTags`
    * Type: aws:executeAwsApi
    * Inputs:
        * `Service`: dynamodb
        * `Api`: TagResource
        * `ResourceArn`: pass `TargetTableArn` value from the `RestoreDynamoDBTableFromBackup` step
        * `Tags`: pass `SourceTableTags` value from the previous step
    * Outputs: None
    * Explanation:
        * Update the list of tags for the target dynamodb table. [tag_resource](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_TagResource.html#API_TagResource_ResponseElements) method
   
1. `GetSourceDynamoDBTableContributorInsights`
    * Type: aws:executeScript
    * Inputs:
        * `TableName`: pass DynamoDBSourceTableName parameter
        * `IndexName`: pass DynamoDBSourceTableIndexName parameter
    * Outputs:
        * `SourceTableContributorInsightsStatus`: The dynamoDB source table contributor insights status: enabled or disabled
    * Explanation:
        * Get the status of dynamoDB source table contributor insights status as they are not restored by the backup. If the value of the `IndexName` parameter is 'None', we call the [describe_contributor_insights](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_DescribeContributorInsights.html) method using only the `TableName` parameter. Otherwise, we call it using both parameters.

1. `CheckSourceDynamoDBTableContributorInsightsStatus`
    * Type: aws:branch
    * Inputs:
        * `SourceTableContributorInsightsStatus`: pass `SourceTableContributorInsightsStatus` value from the previous step
    * Outputs: none
    * Default: Go to the step `GetSourceDynamoDBTablePointInTimeRecoveryStatus`
    * Explanation:
        * If `SourceTableContributorInsightsStatus` is enabled, go to the step `EnableTargetDynamoDBTableContributorInsights`. Otherwise, it will go to the default step.

1. `EnableTargetDynamoDBTableContributorInsights`
    * Type: aws:executeScript
    * Inputs:
        * `TableName`: pass DynamoDBTargetTableName value parameter
        * `ContributorInsightsAction`: needs to be equal to ENABLE
        * `IndexName`: pass DynamoDBTargetTableIndexName parameter
    * Outputs:
        * `TargetTableContributorInsightsStatus`: The dynamoDB target table contributor insights status: enabled or disabled
    * Explanation:
        * Enable the contributor insights status for the target dynamodb table. If the value of the `IndexName` parameter is 'None', we call the [update_contributor_insights](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html#DynamoDB.Client.update_contributor_insights) method using only the `TableName` and `ContributorInsightsAction` parameters. Otherwise, we call it using the three parameters.

1. `GetSourceDynamoDBTablePointInTimeRecoveryStatus`
    * Type: aws:executeAwsApi
    * Inputs:
        * `Service`: dynamodb
        * `Api`: DescribeContinuousBackups
        * `TableName`: pass DynamoDBSourceTableName parameter
    * Outputs:
        * `SourceTablePointInTimeRecoveryStatus`: The dynamoDB source table point in time recovery status: enabled or disabled
    * Explanation:
        * Get the status of dynamoDB source table point in time recovery status as they are not restored by the backup.
          [describe_continuous_backups](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_DescribeContinuousBackups.html) method

1. `CheckSourceDynamoDBTablePointInTimeRecoveryStatus`
    * Type: aws:branch
    * Inputs:
        * `SourceTablePointInTimeRecoveryStatus`: pass `SourceTablePointInTimeRecoveryStatus` value from the previous step
    * Outputs: none
    * Default: Go to the step `GetSourceDynamoDBTableAutoScalingPoliciesAndUpdateTargetDynamoDBTableAutoScalingPolicies`
    * Explanation:
        * If `SourceTablePointInTimeRecoveryStatus` is enabled, go to the step `EnableTargetDynamoDBTablePointInTimeRecoveryStatus`. Otherwise, it will go to the default step.

1. `EnableTargetDynamoDBTablePointInTimeRecoveryStatus`
    * Type: aws:executeAwsApi
    * Inputs:
        * `Service`: dynamodb
        * `Api`: UpdateContinuousBackups
        * `TableName`: pass DynamoDBSourceTableName value parameter
        * `PointInTimeRecoverySpecification`: pass the `True` value to the `PointInTimeRecoveryEnabled` property
    * Outputs:
        * `TargetTablePointInTimeRecoveryStatus`: The dynamoDB target table point in time recovery status: enabled or disabled
    * Explanation:
        * Enable the point in time recovery status for the target dynamodb table.
          [update_continuous_backups](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_UpdateContinuousBackups.html) method

1. `GetSourceDynamoDBTableAutoScalingPoliciesAndUpdateTargetDynamoDBTableAutoScalingPolicies`
    * Type: aws:executeScript
    * Inputs:
        * `AppASGDynamoDBIamRole`: pass the AppASGDynamoDBIamRole parameter
        * `SourceTableId`: pass `table/{{ DynamoDBSourceTableName }}`
    * Outputs:
        * `SourceTableScalableDimensions`: The dynamoDB source table scalable dimensions if exist: dynamodb:table:ReadCapacityUnits, dynamodb:table:WriteCapacityUnits, dynamodb:index:ReadCapacityUnits
          and/or dynamodb:index:WriteCapacityUnits
    * Explanation:
        * Check if the application autoscaling group has the dynamodb source table as a scalable
          target. [describe_scalable_targets](https://boto3.amazonaws.com/v1/documentation/api/1.9.42/reference/services/application-autoscaling.html#ApplicationAutoScaling.Client.describe_scalable_targets)
          method
        * If yes:
            * get the `ScalableDimension`, the `MinCapacity` and the `MaxCapacity` properties for each
              dimension. [describe_scalable_targets](https://boto3.amazonaws.com/v1/documentation/api/1.9.42/reference/services/application-autoscaling.html#ApplicationAutoScaling.Client.describe_scalable_targets)
              method
            * Register the dynamodb target table as a scalable target and pass the `ScalableDimension` the `MinCapacity` and the `MaxCapacity` properties for each dimension's so that the application
              autoscaling group can scale out and scale
              in. [register_scalable_target](https://boto3.amazonaws.com/v1/documentation/api/1.9.42/reference/services/application-autoscaling.html#ApplicationAutoScaling.Client.register_scalable_target)
              method

1. `GetSourceDynamoDBTableAlarmsAndUpdateTargetDynamoDBTableAlarms`
    * Type: aws:executeScript
    * Inputs:
        * `SourceTableAlarmNames`: pass DynamoDBSourceTableAlarmNames parameter
        * `TargetTableName`: pass DynamoDBTargetTableName parameter
    * Outputs:
        * `SourceTableMetricAlarmArns`: The dynamoDB source table list of metric alarm arns from the `MetricAlarms` property
        * `TargetTableMetricAlarmArns`: The dynamoDB target table list of metric alarm arns from the `MetricAlarms` property
    * Explanation:
        * Check if the list of dynamodb source table alarm names is not empty and get the alarm description details for each alarm name. [describe_alarms](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudwatch.html#CloudWatch.Client.describe_alarms) method
        * Get the `MetricAlarms` list property for each alarm name and put it as input for the dynamodb target table alarm and change the dimension to the dynamodb target table name. [put_metric_alarm](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudwatch.html#CloudWatch.Client.put_metric_alarm) method

1. `CheckSourceDynamoDBGlobalTableStatus`
    * Type: aws:branch
    * Inputs:
        * `DynamoDBSourceGlobalTableName`: pass the DynamoDBSourceGlobalTableName parameter
    * Outputs: none
    * Default: Go to the step `RecoveryTime`
    * Explanation:
        * If `DynamoDBSourceGlobalTableName` is not None, go to the step `GetSourceGlobalTableReplicationGroup`. Otherwise, it will go to the default step.

1. `GetSourceGlobalTableReplicationGroup`
    * Type: aws:executeAwsApi
    * Inputs:
        * `Service`: dynamodb
        * `Api`: DescribeGlobalTable
        * `GlobalTableName`: pass DynamoDBSourceGlobalTableName value parameter
    * Outputs:
        * `SourceGlobalTableReplicationGroup`: The dynamoDB source global table replication group from the `GlobalTableDescription` property
        * `SourceGlobalTableStatus`: The dynamoDB source global table status from the `GlobalTableDescription` property
    * Explanation:
        * Get the dynamodb source global table replication group and status from `GlobalTableDescription` property.
          [describe_global_table](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_DescribeGlobalTable.html) method

1. `CheckSourceGlobalTableStatus`
    * Type: aws:branch
    * Inputs:
        * `SourceGlobalTableStatus`: pass the `SourceGlobalTableStatus` from the previous step
    * Outputs: none
    * Default: Go to the step `RecoveryTime`
    * Explanation:
        * If `SourceGlobalTableStatus` is ACTIVE, go to the step `CreateTargetDynamoDBGlobalTable`. Otherwise, it will go to the default step.

1. `CreateTargetDynamoDBGlobalTable`
    * Type: aws:executeAwsApi
    * Inputs:
        * `Service`: dynamodb
        * `Api`: CreateGlobalTable
        * `GlobalTableName`: pass DynamoDBTargetGlobalTableName value parameter
        * `ReplicationGroup`: pass `SourceGlobalTableReplicationGroup` value from the previous step
    * Outputs:
        * `TargetGlobalTableArn`: The dynamoDB target global table arn
    * Explanation:
        * Create the dynamodb target global table. [create_global_table](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_CreateGlobalTable.html) method

1. `VerifyDynamoDBGlobalTableTargetStatusAfterCreateTargetDynamoDBGlobalTable`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `Service`: dynamodb
        * `Api`: DescribeGlobalTable
        * `TableName`: pass DynamoDBTargetGlobalTableName parameter
        * `PropertySelector`: use the $.Table.TableStatus selector
        * `DesiredValues`: needs to be in ACTIVE status
    * Explanation:
        * Wait for the dynamodb target global table to be in ACTIVE status. [describe_global_table](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_DescribeGlobalTable.html) method
        * Use the shared SSM Document as the step to avoid duplicates

1. `OutputRecoveryTime`
    * Type: aws:executeScript
    * Inputs:
        * `StartExecutionTime`: pass `StartExecutionTime` value from the `RecordStartTime` step
    * Outputs:
        * `RecoveryTime`: The time difference between the first step and last step for recovery (RTO).
    * Explanation:
        * Calculate the time difference it takes to recover the dynamodb target table from the source table

## Outputs

* `RestoreDynamoDBTableFromBackup.TargetTableArn`: The ARN of the target table restored from the backup
* `OutputRecoveryTime.RecoveryTime`: The time difference between the first step and last step for recovery (RTO)
* `RestoreDynamoDBTableFromBackup.RecoveryPoint`: the recovery point objective (RPO)