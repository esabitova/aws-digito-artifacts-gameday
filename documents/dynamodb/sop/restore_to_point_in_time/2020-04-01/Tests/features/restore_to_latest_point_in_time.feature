@dynamodb
Feature: SSM automation document to restore the database from point in time.

  Scenario: Restores table to the latest available point
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                       | ResourceType |
      | resource_manager/cloud_formation_templates/DynamoDBTemplate.yml                                       | ON_DEMAND    |
      | documents/dynamodb/sop/restore_to_point_in_time/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestoreToPointInTime_2020-04-01" SSM document
    And published "Digito-CopyDynamoDBTableProperties_2020-04-01" SSM document
    And generate and cache random string with prefix digito_target_table as TargetTableToRestoreName
    And wait table {{cfn-output:DynamoDBTemplate>DynamoDBTable}} to be active for 300 seconds with interval 20 seconds
    And register cleanup steps for table {{cache:TargetTableToRestoreName}} with global table secondary region None
    When SSM automation document "Digito-RestoreToPointInTime_2020-04-01" executed
      | DynamoDBTableSourceName                       | DynamoDBTableTargetName            | AutomationAssumeRole                                                               |
      | {{cfn-output:DynamoDBTemplate>DynamoDBTable}} | {{cache:TargetTableToRestoreName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoDynamodbRestoreFromPointInTimeAssumeRole}} |
    Then SSM automation document "Digito-RestoreToPointInTime_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And assert continuous backups settings copied from {{cfn-output:DynamoDBTemplate>DynamoDBTable}} to {{cache:TargetTableToRestoreName}}


  Scenario: Restores table to the latest available point. With GlobalTable
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                       | ResourceType |
      | resource_manager/cloud_formation_templates/DynamoDBTemplate.yml                                       | ON_DEMAND    |
      | documents/dynamodb/sop/restore_to_point_in_time/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestoreToPointInTime_2020-04-01" SSM document
    And published "Digito-CopyDynamoDBTableProperties_2020-04-01" SSM document
    And generate and cache random string with prefix digito_target_table as TargetTableToRestoreName
    And the cached input parameters
      | GlobalTableSecondaryRegion |
      | ap-southeast-1             |
    And register cleanup steps for table {{cache:TargetTableToRestoreName}} with global table secondary region {{cache:GlobalTableSecondaryRegion}}
    And enabled global dynamodb table {{cfn-output:DynamoDBTemplate>DynamoDBTable}} in the region {{cache:GlobalTableSecondaryRegion}} and wait for 1200 seconds with delay 20 seconds
    And wait table {{cfn-output:DynamoDBTemplate>DynamoDBTable}} to be active for 300 seconds with interval 20 seconds
    When SSM automation document "Digito-RestoreToPointInTime_2020-04-01" executed
      | DynamoDBTableSourceName                       | DynamoDBTableTargetName            | AutomationAssumeRole                                                               |
      | {{cfn-output:DynamoDBTemplate>DynamoDBTable}} | {{cache:TargetTableToRestoreName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoDynamodbRestoreFromPointInTimeAssumeRole}} |
    Then SSM automation document "Digito-RestoreToPointInTime_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And assert global table region {{cache:GlobalTableSecondaryRegion}} copied for table {{cache:TargetTableToRestoreName}}

  Scenario: Restores table to the latest available point. With Scaling
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                       | ResourceType |
      | resource_manager/cloud_formation_templates/dedicated/DynamoDBTemplateWithAutoScaling.yml              | DEDICATED    |
      | documents/dynamodb/sop/restore_to_point_in_time/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestoreToPointInTime_2020-04-01" SSM document
    And published "Digito-CopyDynamoDBTableProperties_2020-04-01" SSM document
    And generate and cache random string with prefix digito_target_table as TargetTableToRestoreName
    And register cleanup steps for table {{cache:TargetTableToRestoreName}} with global table secondary region None
    And wait table {{cfn-output:DynamoDBTemplateWithAutoScaling>DynamoDBTable}} to be active for 300 seconds with interval 20 seconds
    When SSM automation document "Digito-RestoreToPointInTime_2020-04-01" executed
      | DynamoDBTableSourceName                                      | DynamoDBTableTargetName            | AutomationAssumeRole                                                               |
      | {{cfn-output:DynamoDBTemplateWithAutoScaling>DynamoDBTable}} | {{cache:TargetTableToRestoreName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoDynamodbRestoreFromPointInTimeAssumeRole}} |
    Then SSM automation document "Digito-RestoreToPointInTime_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And assert scaling targets copied from {{cfn-output:DynamoDBTemplateWithAutoScaling>DynamoDBTable}} to {{cache:TargetTableToRestoreName}}

  Scenario: Restores table to the latest available point. Copy Alarms
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                       | ResourceType |
      | resource_manager/cloud_formation_templates/DynamoDBTemplate.yml                                       | ON_DEMAND    |
      | documents/dynamodb/sop/restore_to_point_in_time/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestoreToPointInTime_2020-04-01" SSM document
    And published "Digito-CopyDynamoDBTableProperties_2020-04-01" SSM document
    And generate and cache random string with prefix digito_target_table as TargetTableToRestoreName
    And wait table {{cfn-output:DynamoDBTemplate>DynamoDBTable}} to be active for 300 seconds with interval 20 seconds
    And register cleanup steps for table {{cache:TargetTableToRestoreName}} with global table secondary region None
    When SSM automation document "Digito-RestoreToPointInTime_2020-04-01" executed
      | DynamoDBTableSourceName                       | DynamoDBTableTargetName            | AutomationAssumeRole                                                               | DynamoDBSourceTableAlarmNames                                |
      | {{cfn-output:DynamoDBTemplate>DynamoDBTable}} | {{cache:TargetTableToRestoreName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoDynamodbRestoreFromPointInTimeAssumeRole}} | {{cfn-output:DynamoDBTemplate>WriteThrottleEventsAlarmName}} |
    Then SSM automation document "Digito-RestoreToPointInTime_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And assert alarm {{cfn-output:DynamoDBTemplate>WriteThrottleEventsAlarmName}} copied for table {{cache:TargetTableToRestoreName}}

  Scenario: Restores table to the latest available point. With Indexes
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                       | ResourceType |
      | resource_manager/cloud_formation_templates/DynamoDBTemplateWithIndex.yml                              | ON_DEMAND    |
      | documents/dynamodb/sop/restore_to_point_in_time/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestoreToPointInTime_2020-04-01" SSM document
    And published "Digito-CopyDynamoDBTableProperties_2020-04-01" SSM document
    And generate and cache random string with prefix digito_target_table as TargetTableToRestoreName
    And wait table {{cfn-output:DynamoDBTemplateWithIndex>DynamoDBTable}} to be active for 300 seconds with interval 20 seconds
    And register cleanup steps for table {{cache:TargetTableToRestoreName}} with global table secondary region None
    When SSM automation document "Digito-RestoreToPointInTime_2020-04-01" executed
      | DynamoDBTableSourceName                                | DynamoDBTableTargetName            | AutomationAssumeRole                                                               |
      | {{cfn-output:DynamoDBTemplateWithIndex>DynamoDBTable}} | {{cache:TargetTableToRestoreName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoDynamodbRestoreFromPointInTimeAssumeRole}} |
    Then SSM automation document "Digito-RestoreToPointInTime_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And assert indexes copied from {{cfn-output:DynamoDBTemplateWithIndex>DynamoDBTable}} to {{cache:TargetTableToRestoreName}}

  Scenario: Restores table to the latest available point. With Indexes and contributor insights enabled
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                       | ResourceType |
      | resource_manager/cloud_formation_templates/DynamoDBTemplateWithIndexAndContributorInsights.yml        | ON_DEMAND    |
      | documents/dynamodb/sop/restore_to_point_in_time/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestoreToPointInTime_2020-04-01" SSM document
    And published "Digito-CopyDynamoDBTableProperties_2020-04-01" SSM document
    And generate and cache random string with prefix digito_target_table as TargetTableToRestoreName
    And register cleanup steps for table {{cache:TargetTableToRestoreName}} with global table secondary region None
    And wait table {{cfn-output:DynamoDBTemplateWithIndexAndContributorInsights>DynamoDBTable}} to be active for 300 seconds with interval 20 seconds
    When SSM automation document "Digito-RestoreToPointInTime_2020-04-01" executed
      | DynamoDBTableSourceName                                                      | DynamoDBTableTargetName            | AutomationAssumeRole                                                               |
      | {{cfn-output:DynamoDBTemplateWithIndexAndContributorInsights>DynamoDBTable}} | {{cache:TargetTableToRestoreName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoDynamodbRestoreFromPointInTimeAssumeRole}} |
    Then SSM automation document "Digito-RestoreToPointInTime_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And assert indexes copied from {{cfn-output:DynamoDBTemplateWithIndexAndContributorInsights>DynamoDBTable}} to {{cache:TargetTableToRestoreName}}
    And assert contributor insights copied from {{cfn-output:DynamoDBTemplateWithIndexAndContributorInsights>DynamoDBTable}} to {{cache:TargetTableToRestoreName}}


  Scenario: Restores table to the latest available point. In the source table the stream is enabled
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                       | ResourceType |
      | resource_manager/cloud_formation_templates/DynamoDBTemplateWithStream.yml                             | ON_DEMAND    |
      | documents/dynamodb/sop/restore_to_point_in_time/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestoreToPointInTime_2020-04-01" SSM document
    And published "Digito-CopyDynamoDBTableProperties_2020-04-01" SSM document
    And generate and cache random string with prefix digito_target_table as TargetTableToRestoreName
    And wait table {{cfn-output:DynamoDBTemplateWithStream>DynamoDBTable}} to be active for 300 seconds with interval 20 seconds
    And register cleanup steps for table {{cache:TargetTableToRestoreName}} with global table secondary region None
    When SSM automation document "Digito-RestoreToPointInTime_2020-04-01" executed
      | DynamoDBTableSourceName                                 | DynamoDBTableTargetName            | AutomationAssumeRole                                                               |
      | {{cfn-output:DynamoDBTemplateWithStream>DynamoDBTable}} | {{cache:TargetTableToRestoreName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoDynamodbRestoreFromPointInTimeAssumeRole}} |
    Then SSM automation document "Digito-RestoreToPointInTime_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And assert stream copied from {{cfn-output:DynamoDBTemplateWithStream>DynamoDBTable}} to {{cache:TargetTableToRestoreName}}

  Scenario: Restores table to the latest available point with enabled kinesis streaming destination
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                       | ResourceType | KmsKey                              |
      | resource_manager/cloud_formation_templates/shared/KMS.yml                                             | SHARED       |                                     |
      | resource_manager/cloud_formation_templates/DynamoDBTemplateWithKinesis.yml                            | ON_DEMAND    | {{cfn-output:KMS>EncryptAtRestKey}} |
      | documents/dynamodb/sop/restore_to_point_in_time/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                                     |
    And published "Digito-RestoreToPointInTime_2020-04-01" SSM document
    And published "Digito-CopyDynamoDBTableProperties_2020-04-01" SSM document
    And generate and cache random string with prefix digito_target_table as TargetTableToRestoreName
    And wait table {{cfn-output:DynamoDBTemplateWithKinesis>DynamoDBTable}} to be active for 300 seconds with interval 20 seconds
    And register cleanup steps for table {{cache:TargetTableToRestoreName}} with global table secondary region None
    When SSM automation document "Digito-RestoreToPointInTime_2020-04-01" executed
      | DynamoDBTableSourceName                                  | DynamoDBTableTargetName            | AutomationAssumeRole                                                               |
      | {{cfn-output:DynamoDBTemplateWithKinesis>DynamoDBTable}} | {{cache:TargetTableToRestoreName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoDynamodbRestoreFromPointInTimeAssumeRole}} |
    Then SSM automation document "Digito-RestoreToPointInTime_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And assert kinesis destinations copied from {{cfn-output:DynamoDBTemplateWithKinesis>DynamoDBTable}} to {{cache:TargetTableToRestoreName}}


  Scenario: Restores table to the latest available point with TTL enabled
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                       | ResourceType |
      | resource_manager/cloud_formation_templates/DynamoDBTemplateWithTtl.yml                                | ON_DEMAND    |
      | documents/dynamodb/sop/restore_to_point_in_time/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestoreToPointInTime_2020-04-01" SSM document
    And published "Digito-CopyDynamoDBTableProperties_2020-04-01" SSM document
    And generate and cache random string with prefix digito_target_table as TargetTableToRestoreName
    And wait table {{cfn-output:DynamoDBTemplateWithTtl>DynamoDBTable}} to be active for 300 seconds with interval 20 seconds
    And register cleanup steps for table {{cache:TargetTableToRestoreName}} with global table secondary region None
    When SSM automation document "Digito-RestoreToPointInTime_2020-04-01" executed
      | DynamoDBTableSourceName                              | DynamoDBTableTargetName            | AutomationAssumeRole                                                               |
      | {{cfn-output:DynamoDBTemplateWithTtl>DynamoDBTable}} | {{cache:TargetTableToRestoreName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoDynamodbRestoreFromPointInTimeAssumeRole}} |
    Then SSM automation document "Digito-RestoreToPointInTime_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And assert time-to-live copied from {{cfn-output:DynamoDBTemplateWithTtl>DynamoDBTable}} to {{cache:TargetTableToRestoreName}}
