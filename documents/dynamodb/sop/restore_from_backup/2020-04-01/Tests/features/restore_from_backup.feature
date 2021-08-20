@dynamodb
Feature: SSM automation document to restore the database from a backup.

  Scenario: Restores table from backup
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                  | ResourceType |
      | resource_manager/cloud_formation_templates/DynamoDBTemplate.yml                                  | ON_DEMAND    |
      | documents/dynamodb/sop/restore_from_backup/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestoreFromBackup_2020-04-01" SSM document
    And generate and cache random string with prefix digito_target_table as TargetTableToRestoreName
    And generate and cache random string with prefix digito_test_backup as BackupName
    And wait table {{cfn-output:DynamoDBTemplate>DynamoDBTable}} to be active for 300 seconds with interval 20 seconds
    And register cleanup steps for table {{cache:TargetTableToRestoreName}} with global table secondary region None
    And Create backup {{cache:BackupName}} for table {{cfn-output:DynamoDBTemplate>DynamoDBTable}} and wait for 600 seconds with interval 20 seconds
    When SSM automation document "Digito-RestoreFromBackup_2020-04-01" executed
      | DynamoDBTableSourceName                       | DynamoDBTableTargetName            | DynamoDBSourceTableBackupArn | AutomationAssumeRole                                                                 |
      | {{cfn-output:DynamoDBTemplate>DynamoDBTable}} | {{cache:TargetTableToRestoreName}} | {{cache:BackupArn}}          | {{cfn-output:AutomationAssumeRoleTemplate>DigitoDynamodbRestoreFromBackupAssumeRole}}|
    Then SSM automation document "Digito-RestoreFromBackup_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

  Scenario: Restores table from backup. Stream Enabled
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                  | ResourceType |
      | resource_manager/cloud_formation_templates/DynamoDBTemplateWithStream.yml                        | ON_DEMAND    |
      | documents/dynamodb/sop/restore_from_backup/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestoreFromBackup_2020-04-01" SSM document
    And generate and cache random string with prefix digito_target_table as TargetTableToRestoreName
    And generate and cache random string with prefix digito_test_backup as BackupName
    And wait table {{cfn-output:DynamoDBTemplateWithStream>DynamoDBTable}} to be active for 300 seconds with interval 20 seconds
    And register cleanup steps for table {{cache:TargetTableToRestoreName}} with global table secondary region None
    And Create backup {{cache:BackupName}} for table {{cfn-output:DynamoDBTemplateWithStream>DynamoDBTable}} and wait for 600 seconds with interval 20 seconds
    When SSM automation document "Digito-RestoreFromBackup_2020-04-01" executed
      | DynamoDBTableSourceName                                    | DynamoDBTableTargetName            | DynamoDBSourceTableBackupArn | AutomationAssumeRole                                                               |
      | {{cfn-output:DynamoDBTemplateWithStream>DynamoDBTable}} | {{cache:TargetTableToRestoreName}} | {{cache:BackupArn}}          | {{cfn-output:AutomationAssumeRoleTemplate>DigitoDynamodbRestoreFromBackupAssumeRole}} |
    Then SSM automation document "Digito-RestoreFromBackup_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And assert stream copied from {{cfn-output:DynamoDBTemplateWithStream>DynamoDBTable}} to {{cache:TargetTableToRestoreName}}


  Scenario: Restores table from backup. Kinesis Enabled
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                  | ResourceType | KmsKey                              |
      | resource_manager/cloud_formation_templates/shared/KMS.yml                                        | SHARED       |                                     |
      | resource_manager/cloud_formation_templates/DynamoDBTemplateWithKinesis.yml                       | ON_DEMAND    | {{cfn-output:KMS>EncryptAtRestKey}} |
      | documents/dynamodb/sop/restore_from_backup/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                                     |
    And published "Digito-RestoreFromBackup_2020-04-01" SSM document
    And published "Digito-CopyDynamoDBTableProperties_2020-04-01" SSM document
    And generate and cache random string with prefix digito_target_table as TargetTableToRestoreName
    And generate and cache random string with prefix digito_test_backup as BackupName
    And wait table {{cfn-output:DynamoDBTemplateWithKinesis>DynamoDBTable}} to be active for 300 seconds with interval 20 seconds
    And register cleanup steps for table {{cache:TargetTableToRestoreName}} with global table secondary region None
    And Create backup {{cache:BackupName}} for table {{cfn-output:DynamoDBTemplateWithKinesis>DynamoDBTable}} and wait for 600 seconds with interval 20 seconds
    When SSM automation document "Digito-RestoreFromBackup_2020-04-01" executed
      | DynamoDBTableSourceName                                  | DynamoDBTableTargetName            | DynamoDBSourceTableBackupArn | AutomationAssumeRole                                                               |
      | {{cfn-output:DynamoDBTemplateWithKinesis>DynamoDBTable}} | {{cache:TargetTableToRestoreName}} | {{cache:BackupArn}}          | {{cfn-output:AutomationAssumeRoleTemplate>DigitoDynamodbRestoreFromBackupAssumeRole}} |
    Then SSM automation document "Digito-RestoreFromBackup_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And assert kinesis destinations copied from {{cfn-output:DynamoDBTemplateWithKinesis>DynamoDBTable}} to {{cache:TargetTableToRestoreName}}


  Scenario: Restores table from backup. Contributor Insights
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                  | ResourceType |
      | resource_manager/cloud_formation_templates/DynamoDBTemplateWithIndexAndContributorInsights.yml   | ON_DEMAND    |
      | documents/dynamodb/sop/restore_from_backup/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestoreFromBackup_2020-04-01" SSM document
    And generate and cache random string with prefix digito_target_table as TargetTableToRestoreName
    And generate and cache random string with prefix digito_test_backup as BackupName
    And wait table {{cfn-output:DynamoDBTemplateWithIndexAndContributorInsights>DynamoDBTable}} to be active for 300 seconds with interval 20 seconds
    And register cleanup steps for table {{cache:TargetTableToRestoreName}} with global table secondary region None
    And Create backup {{cache:BackupName}} for table {{cfn-output:DynamoDBTemplateWithIndexAndContributorInsights>DynamoDBTable}} and wait for 600 seconds with interval 20 seconds
    When SSM automation document "Digito-RestoreFromBackup_2020-04-01" executed
      | DynamoDBTableSourceName                                                      | DynamoDBTableTargetName            | DynamoDBSourceTableBackupArn | AutomationAssumeRole                                                               |
      | {{cfn-output:DynamoDBTemplateWithIndexAndContributorInsights>DynamoDBTable}} | {{cache:TargetTableToRestoreName}} | {{cache:BackupArn}}          | {{cfn-output:AutomationAssumeRoleTemplate>DigitoDynamodbRestoreFromBackupAssumeRole}} |
    Then SSM automation document "Digito-RestoreFromBackup_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And assert indexes copied from {{cfn-output:DynamoDBTemplateWithIndexAndContributorInsights>DynamoDBTable}} to {{cache:TargetTableToRestoreName}}
    And assert contributor insights copied from {{cfn-output:DynamoDBTemplateWithIndexAndContributorInsights>DynamoDBTable}} to {{cache:TargetTableToRestoreName}}


  Scenario: Restores table from backup. With Autoscaling
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                  | ResourceType |
      | resource_manager/cloud_formation_templates/dedicated/DynamoDBTemplateWithAutoScaling.yml         | DEDICATED    |
      | documents/dynamodb/sop/restore_from_backup/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestoreFromBackup_2020-04-01" SSM document
    And generate and cache random string with prefix digito_target_table as TargetTableToRestoreName
    And generate and cache random string with prefix digito_test_backup as BackupName
    And wait table {{cfn-output:DynamoDBTemplateWithAutoScaling>DynamoDBTable}} to be active for 300 seconds with interval 20 seconds
    And register cleanup steps for table {{cache:TargetTableToRestoreName}} with global table secondary region None
    And Create backup {{cache:BackupName}} for table {{cfn-output:DynamoDBTemplateWithAutoScaling>DynamoDBTable}} and wait for 600 seconds with interval 20 seconds
    When SSM automation document "Digito-RestoreFromBackup_2020-04-01" executed
      | DynamoDBTableSourceName                                      | DynamoDBTableTargetName            | DynamoDBSourceTableBackupArn | AutomationAssumeRole                                                               |
      | {{cfn-output:DynamoDBTemplateWithAutoScaling>DynamoDBTable}} | {{cache:TargetTableToRestoreName}} | {{cache:BackupArn}}          | {{cfn-output:AutomationAssumeRoleTemplate>DigitoDynamodbRestoreFromBackupAssumeRole}} |
    Then SSM automation document "Digito-RestoreFromBackup_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And assert scaling targets copied from {{cfn-output:DynamoDBTemplateWithAutoScaling>DynamoDBTable}} to {{cache:TargetTableToRestoreName}}


  Scenario: Restores table from backup. Global Table
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                  | ResourceType |
      | resource_manager/cloud_formation_templates/DynamoDBTemplate.yml                                  | ON_DEMAND    |
      | documents/dynamodb/sop/restore_from_backup/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestoreFromBackup_2020-04-01" SSM document
    And generate and cache random string with prefix digito_target_table as TargetTableToRestoreName
    And generate and cache random string with prefix digito_test_backup as BackupName
    And wait table {{cfn-output:DynamoDBTemplate>DynamoDBTable}} to be active for 300 seconds with interval 20 seconds
    And the cached input parameters
      | GlobalTableSecondaryRegion |
      | ap-southeast-1             |
    And enabled global dynamodb table {{cfn-output:DynamoDBTemplate>DynamoDBTable}} in the region {{cache:GlobalTableSecondaryRegion}} and wait for 1800 seconds with delay 20 seconds
    And register cleanup steps for table {{cache:TargetTableToRestoreName}} with global table secondary region {{cache:GlobalTableSecondaryRegion}}
    And Create backup {{cache:BackupName}} for table {{cfn-output:DynamoDBTemplate>DynamoDBTable}} and wait for 600 seconds with interval 20 seconds
    When SSM automation document "Digito-RestoreFromBackup_2020-04-01" executed
      | DynamoDBTableSourceName                       | DynamoDBTableTargetName            | DynamoDBSourceTableBackupArn | AutomationAssumeRole                                                                 |
      | {{cfn-output:DynamoDBTemplate>DynamoDBTable}} | {{cache:TargetTableToRestoreName}} | {{cache:BackupArn}}          | {{cfn-output:AutomationAssumeRoleTemplate>DigitoDynamodbRestoreFromBackupAssumeRole}}|
    Then SSM automation document "Digito-RestoreFromBackup_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And assert global table region {{cache:GlobalTableSecondaryRegion}} copied for table {{cache:TargetTableToRestoreName}}


  Scenario: Restores table from backup with TTL enabled
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                  | ResourceType |
      | resource_manager/cloud_formation_templates/DynamoDBTemplateWithTtl.yml                           | ON_DEMAND    |
      | documents/dynamodb/sop/restore_from_backup/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestoreFromBackup_2020-04-01" SSM document
    And published "Digito-CopyDynamoDBTableProperties_2020-04-01" SSM document
    And generate and cache random string with prefix digito_target_table as TargetTableToRestoreName
    And generate and cache random string with prefix digito_test_backup as BackupName
    And wait table {{cfn-output:DynamoDBTemplateWithTtl>DynamoDBTable}} to be active for 300 seconds with interval 20 seconds
    And register cleanup steps for table {{cache:TargetTableToRestoreName}} with global table secondary region None
    And Create backup {{cache:BackupName}} for table {{cfn-output:DynamoDBTemplateWithTtl>DynamoDBTable}} and wait for 600 seconds with interval 20 seconds
    When SSM automation document "Digito-RestoreFromBackup_2020-04-01" executed
      | DynamoDBTableSourceName                              | DynamoDBTableTargetName            | DynamoDBSourceTableBackupArn | AutomationAssumeRole                                                                 |
      | {{cfn-output:DynamoDBTemplateWithTtl>DynamoDBTable}} | {{cache:TargetTableToRestoreName}} | {{cache:BackupArn}}          | {{cfn-output:AutomationAssumeRoleTemplate>DigitoDynamodbRestoreFromBackupAssumeRole}}|
    Then SSM automation document "Digito-RestoreFromBackup_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And assert time-to-live copied from {{cfn-output:DynamoDBTemplateWithTtl>DynamoDBTable}} to {{cache:TargetTableToRestoreName}}


  Scenario: Restores table to the latest available point. Copy Alarms
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                  | ResourceType |
      | resource_manager/cloud_formation_templates/DynamoDBTemplate.yml                                  | ON_DEMAND    |
      | documents/dynamodb/sop/restore_from_backup/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestoreFromBackup_2020-04-01" SSM document
    And published "Digito-CopyDynamoDBTableProperties_2020-04-01" SSM document
    And generate and cache random string with prefix digito_target_table as TargetTableToRestoreName
    And generate and cache random string with prefix digito_test_backup as BackupName
    And wait table {{cfn-output:DynamoDBTemplate>DynamoDBTable}} to be active for 300 seconds with interval 20 seconds
    And register cleanup steps for table {{cache:TargetTableToRestoreName}} with global table secondary region None
    And Create backup {{cache:BackupName}} for table {{cfn-output:DynamoDBTemplate>DynamoDBTable}} and wait for 600 seconds with interval 20 seconds
    When SSM automation document "Digito-RestoreFromBackup_2020-04-01" executed
      | DynamoDBTableSourceName                       | DynamoDBTableTargetName            | DynamoDBSourceTableBackupArn | AutomationAssumeRole                                                                  | DynamoDBSourceTableAlarmNames                                |
      | {{cfn-output:DynamoDBTemplate>DynamoDBTable}} | {{cache:TargetTableToRestoreName}} | {{cache:BackupArn}}          | {{cfn-output:AutomationAssumeRoleTemplate>DigitoDynamodbRestoreFromBackupAssumeRole}} | {{cfn-output:DynamoDBTemplate>WriteThrottleEventsAlarmName}} |
    Then SSM automation document "Digito-RestoreFromBackup_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And assert alarm {{cfn-output:DynamoDBTemplate>WriteThrottleEventsAlarmName}} copied for table {{cache:TargetTableToRestoreName}}