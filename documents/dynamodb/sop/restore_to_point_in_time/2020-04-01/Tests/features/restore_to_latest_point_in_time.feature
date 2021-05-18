@dynamodb
Feature: SSM automation document to restore the database from point in time.

  # TODO: validate the all the copied table properties on the target table
  Scenario: Restores table to the latest available point
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                       | ResourceType |
      | resource_manager/cloud_formation_templates/DynamoDBTemplate.yml                                       | ON_DEMAND    |
      | documents/dynamodb/sop/restore_to_point_in_time/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestoreToPointInTime_2020-04-01" SSM document
    And published "Digito-CopyDynamoDBTableProperties_2020-04-01" SSM document
    And generate and cache random string with prefix digito_target_table as TargetTableToRestoreName
    And wait table {{cfn-output:DynamoDBTemplate>DynamoDBTable}} to be active for 300 seconds with interval 20 seconds
    When SSM automation document "Digito-RestoreToPointInTime_2020-04-01" executed
      | DynamoDBTableSourceName                       | DynamoDBTableTargetName            | AutomationAssumeRole                                                               |
      | {{cfn-output:DynamoDBTemplate>DynamoDBTable}} | {{cache:TargetTableToRestoreName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestoreFromPointInTimeAssumeRole}} |
    Then SSM automation document "Digito-RestoreToPointInTime_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And delete all alarms for the table {{cache:TargetTableToRestoreName}}
    And drop Dynamo DB table with the name {{cache:TargetTableToRestoreName}} and wait for 300 seconds with interval 20 seconds

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
    And enabled global dynamodb table {{cfn-output:DynamoDBTemplate>DynamoDBTable}} in the region {{cache:GlobalTableSecondaryRegion}} and wait for 600 seconds with delay 20 seconds
    And wait table {{cfn-output:DynamoDBTemplate>DynamoDBTable}} to be active for 300 seconds with interval 20 seconds
    When SSM automation document "Digito-RestoreToPointInTime_2020-04-01" executed
      | DynamoDBTableSourceName                       | DynamoDBTableTargetName            | AutomationAssumeRole                                                               |
      | {{cfn-output:DynamoDBTemplate>DynamoDBTable}} | {{cache:TargetTableToRestoreName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestoreFromPointInTimeAssumeRole}} |
    Then SSM automation document "Digito-RestoreToPointInTime_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And disable global dynamodb table {{cfn-output:DynamoDBTemplate>DynamoDBTable}} in the region {{cache:GlobalTableSecondaryRegion}} and wait for 600 seconds with delay 20 seconds
    And disable global dynamodb table {{cache:TargetTableToRestoreName}} in the region {{cache:GlobalTableSecondaryRegion}} and wait for 600 seconds with delay 20 seconds
    And delete all alarms for the table {{cache:TargetTableToRestoreName}}
    And drop Dynamo DB table with the name {{cache:TargetTableToRestoreName}} and wait for 300 seconds with interval 20 seconds


  Scenario: Restores table to the latest available point. With Scaling
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                       | ResourceType |
      | resource_manager/cloud_formation_templates/DynamoDBTemplateWithAutoScaling.yml                        | ON_DEMAND    |
      | documents/dynamodb/sop/restore_to_point_in_time/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestoreToPointInTime_2020-04-01" SSM document
    And published "Digito-CopyDynamoDBTableProperties_2020-04-01" SSM document
    And generate and cache random string with prefix digito_target_table as TargetTableToRestoreName
    And wait table {{cfn-output:DynamoDBTemplateWithAutoScaling>DynamoDBTable}} to be active for 300 seconds with interval 20 seconds
    When SSM automation document "Digito-RestoreToPointInTime_2020-04-01" executed
      | DynamoDBTableSourceName                                      | DynamoDBTableTargetName            | AutomationAssumeRole                                                               |
      | {{cfn-output:DynamoDBTemplateWithAutoScaling>DynamoDBTable}} | {{cache:TargetTableToRestoreName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestoreFromPointInTimeAssumeRole}} |
    Then SSM automation document "Digito-RestoreToPointInTime_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And deregister all scaling target for the table {{cache:TargetTableToRestoreName}}
    And delete all alarms for the table {{cache:TargetTableToRestoreName}}
    And drop Dynamo DB table with the name {{cache:TargetTableToRestoreName}} and wait for 300 seconds with interval 20 seconds

  # TODO In this Scenario it would be good to test how many Alarms has been changed (the output of SwitchAlarmsToTargetTable)
  # need to improve current code functionality of the tests by adding appropriate step
  # this will be done in a "Full Cucumber test" task
  Scenario: Restores table to the latest available point. Copy Alarms
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                       | ResourceType |
      | resource_manager/cloud_formation_templates/DynamoDBTemplate.yml                                       | ON_DEMAND    |
      | documents/dynamodb/sop/restore_to_point_in_time/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestoreToPointInTime_2020-04-01" SSM document
    And published "Digito-CopyDynamoDBTableProperties_2020-04-01" SSM document
    And generate and cache random string with prefix digito_target_table as TargetTableToRestoreName
    And wait table {{cfn-output:DynamoDBTemplate>DynamoDBTable}} to be active for 300 seconds with interval 20 seconds
    When SSM automation document "Digito-RestoreToPointInTime_2020-04-01" executed
      | DynamoDBTableSourceName                       | DynamoDBTableTargetName            | AutomationAssumeRole                                                               | DynamoDBSourceTableAlarmNames |
      | {{cfn-output:DynamoDBTemplate>DynamoDBTable}} | {{cache:TargetTableToRestoreName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestoreFromPointInTimeAssumeRole}} | WriteThrottleEvents           |
    Then SSM automation document "Digito-RestoreToPointInTime_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And delete all alarms for the table {{cache:TargetTableToRestoreName}}
    And drop Dynamo DB table with the name {{cache:TargetTableToRestoreName}} and wait for 300 seconds with interval 20 seconds

  Scenario: Restores table to the latest available point. With Indexes
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                       | ResourceType |
      | resource_manager/cloud_formation_templates/DynamoDBTemplateWithIndex.yml                              | ON_DEMAND    |
      | documents/dynamodb/sop/restore_to_point_in_time/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestoreToPointInTime_2020-04-01" SSM document
    And published "Digito-CopyDynamoDBTableProperties_2020-04-01" SSM document
    And generate and cache random string with prefix digito_target_table as TargetTableToRestoreName
    And wait table {{cfn-output:DynamoDBTemplateWithIndex>DynamoDBTable}} to be active for 300 seconds with interval 20 seconds
    When SSM automation document "Digito-RestoreToPointInTime_2020-04-01" executed
      | DynamoDBTableSourceName                                | DynamoDBTableTargetName            | AutomationAssumeRole                                                               |
      | {{cfn-output:DynamoDBTemplateWithIndex>DynamoDBTable}} | {{cache:TargetTableToRestoreName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestoreFromPointInTimeAssumeRole}} |

    Then SSM automation document "Digito-RestoreToPointInTime_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And drop Dynamo DB table with the name {{cache:TargetTableToRestoreName}} and wait for 300 seconds with interval 20 seconds


  Scenario: Restores table to the latest available point. With Indexes and contributor insights enabled
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                       | ResourceType |
      | resource_manager/cloud_formation_templates/DynamoDBTemplateWithIndexAndContributorInsights.yml        | ON_DEMAND    |
      | documents/dynamodb/sop/restore_to_point_in_time/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestoreToPointInTime_2020-04-01" SSM document
    And published "Digito-CopyDynamoDBTableProperties_2020-04-01" SSM document
    And generate and cache random string with prefix digito_target_table as TargetTableToRestoreName
    And wait table {{cfn-output:DynamoDBTemplateWithIndexAndContributorInsights>DynamoDBTable}} to be active for 300 seconds with interval 20 seconds
    When SSM automation document "Digito-RestoreToPointInTime_2020-04-01" executed
      | DynamoDBTableSourceName                                                      | DynamoDBTableTargetName            | AutomationAssumeRole                                                               |
      | {{cfn-output:DynamoDBTemplateWithIndexAndContributorInsights>DynamoDBTable}} | {{cache:TargetTableToRestoreName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestoreFromPointInTimeAssumeRole}} |

    Then SSM automation document "Digito-RestoreToPointInTime_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And drop Dynamo DB table with the name {{cache:TargetTableToRestoreName}} and wait for 300 seconds with interval 20 seconds


  Scenario: Restores table to the latest available point. In the source table the stream is enabled
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                       | ResourceType |
      | resource_manager/cloud_formation_templates/DynamoDBTemplateWithStream.yml                             | ON_DEMAND    |
      | documents/dynamodb/sop/restore_to_point_in_time/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestoreToPointInTime_2020-04-01" SSM document
    And published "Digito-CopyDynamoDBTableProperties_2020-04-01" SSM document
    And generate and cache random string with prefix digito_target_table as TargetTableToRestoreName
    And wait table {{cfn-output:DynamoDBTemplateWithStream>DynamoDBTable}} to be active for 300 seconds with interval 20 seconds
    When SSM automation document "Digito-RestoreToPointInTime_2020-04-01" executed
      | DynamoDBTableSourceName                                 | DynamoDBTableTargetName            | AutomationAssumeRole                                                               |
      | {{cfn-output:DynamoDBTemplateWithStream>DynamoDBTable}} | {{cache:TargetTableToRestoreName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestoreFromPointInTimeAssumeRole}} |

    Then SSM automation document "Digito-RestoreToPointInTime_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And drop Dynamo DB table with the name {{cache:TargetTableToRestoreName}} and wait for 300 seconds with interval 20 seconds


  Scenario: Restores table to the latest available point with enabled kinesis streaming destination
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                       | ResourceType |
      | resource_manager/cloud_formation_templates/DynamoDBTemplateWithKinesis.yml                            | ON_DEMAND    |
      | documents/dynamodb/sop/restore_to_point_in_time/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestoreToPointInTime_2020-04-01" SSM document
    And published "Digito-CopyDynamoDBTableProperties_2020-04-01" SSM document
    And generate and cache random string with prefix digito_target_table as TargetTableToRestoreName
    And wait table {{cfn-output:DynamoDBTemplateWithKinesis>DynamoDBTable}} to be active for 300 seconds with interval 20 seconds
    When SSM automation document "Digito-RestoreToPointInTime_2020-04-01" executed
      | DynamoDBTableSourceName                                  | DynamoDBTableTargetName            | AutomationAssumeRole                                                               |
      | {{cfn-output:DynamoDBTemplateWithKinesis>DynamoDBTable}} | {{cache:TargetTableToRestoreName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestoreFromPointInTimeAssumeRole}} |
    Then SSM automation document "Digito-RestoreToPointInTime_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And drop Dynamo DB table with the name {{cache:TargetTableToRestoreName}} and wait for 300 seconds with interval 20 seconds


  Scenario: Restores table to the latest available point with TTL enabled
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                       | ResourceType |
      | resource_manager/cloud_formation_templates/DynamoDBTemplateWithTtl.yml                                | ON_DEMAND    |
      | documents/dynamodb/sop/restore_to_point_in_time/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestoreToPointInTime_2020-04-01" SSM document
    And published "Digito-CopyDynamoDBTableProperties_2020-04-01" SSM document
    And generate and cache random string with prefix digito_target_table as TargetTableToRestoreName
    And wait table {{cfn-output:DynamoDBTemplateWithTtl>DynamoDBTable}} to be active for 300 seconds with interval 20 seconds
    When SSM automation document "Digito-RestoreToPointInTime_2020-04-01" executed
      | DynamoDBTableSourceName                              | DynamoDBTableTargetName            | AutomationAssumeRole                                                               |
      | {{cfn-output:DynamoDBTemplateWithTtl>DynamoDBTable}} | {{cache:TargetTableToRestoreName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestoreFromPointInTimeAssumeRole}} |
    Then SSM automation document "Digito-RestoreToPointInTime_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And drop Dynamo DB table with the name {{cache:TargetTableToRestoreName}} and wait for 300 seconds with interval 20 seconds


