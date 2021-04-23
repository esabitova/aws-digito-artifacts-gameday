@dynamodb
Feature: SSM automation document to restore the database from point in time.

  Scenario: Restores table to the latest available point
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                       | ResourceType |
      | resource_manager/cloud_formation_templates/DynamoDBTemplate.yml                                       | ON_DEMAND    |
      | documents/dynamodb/sop/restore_to_point_in_time/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestoreToPointInTime_2020-04-01" SSM document
    And the cached input parameters
      | TargetTableToRestoreName |
      | TargetTableToRestore     |
    And drop Dynamo DB table with the name {{cache:TargetTableToRestoreName}} and wait for 300 seconds with interval 20 seconds
    When SSM automation document "Digito-RestoreToPointInTime_2020-04-01" executed
      | DynamoDBTableSourceName                       | DynamoDBTableTargetName            | AutomationAssumeRole                                                               |
      | {{cfn-output:DynamoDBTemplate>DynamoDBTable}} | {{cache:TargetTableToRestoreName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestoreFromPointInTimeAssumeRole}} |
    Then SSM automation document "Digito-RestoreToPointInTime_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And drop Dynamo DB table with the name {{cache:TargetTableToRestoreName}} and wait for 300 seconds with interval 20 seconds

  Scenario: Restores table to the latest available point. With GlobalTable
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                       | ResourceType |
      | resource_manager/cloud_formation_templates/DynamoDBTemplate.yml                                       | ON_DEMAND    |
      | documents/dynamodb/sop/restore_to_point_in_time/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestoreToPointInTime_2020-04-01" SSM document
    And the cached input parameters
      | TargetTableToRestoreName | GlobalTableSecondaryRegion |
      | TargetTableToRestore     | ap-southeast-1             |
    And enabled global dynamodb table {{cfn-output:DynamoDBTemplate>DynamoDBTable}} in the region {{cache:GlobalTableSecondaryRegion}} and wait for 600 seconds with delay 20 seconds
    And drop Dynamo DB table with the name {{cache:TargetTableToRestoreName}} and wait for 300 seconds with interval 20 seconds
    When SSM automation document "Digito-RestoreToPointInTime_2020-04-01" executed
      | DynamoDBTableSourceName                       | DynamoDBTableTargetName            | AutomationAssumeRole                                                               |
      | {{cfn-output:DynamoDBTemplate>DynamoDBTable}} | {{cache:TargetTableToRestoreName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestoreFromPointInTimeAssumeRole}} |
    Then SSM automation document "Digito-RestoreToPointInTime_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And disable global dynamodb table {{cfn-output:DynamoDBTemplate>DynamoDBTable}} in the region {{cache:GlobalTableSecondaryRegion}} and wait for 600 seconds with delay 20 seconds
    And disable global dynamodb table {{cache:TargetTableToRestoreName}} in the region {{cache:GlobalTableSecondaryRegion}} and wait for 600 seconds with delay 20 seconds
    And drop Dynamo DB table with the name {{cache:TargetTableToRestoreName}} and wait for 300 seconds with interval 20 seconds


  Scenario: Restores table to the latest available point. With Scaling
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                       | ResourceType |
      | resource_manager/cloud_formation_templates/DynamoDBTemplateWithAutoScaling.yml                        | ON_DEMAND    |
      | documents/dynamodb/sop/restore_to_point_in_time/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestoreToPointInTime_2020-04-01" SSM document
    And the cached input parameters
      | TargetTableToRestoreName |
      | TargetTableToRestore     |
    And drop Dynamo DB table with the name {{cache:TargetTableToRestoreName}} and wait for 300 seconds with interval 20 seconds
    When SSM automation document "Digito-RestoreToPointInTime_2020-04-01" executed
      | DynamoDBTableSourceName                                      | DynamoDBTableTargetName            | AutomationAssumeRole                                                               |
      | {{cfn-output:DynamoDBTemplateWithAutoScaling>DynamoDBTable}} | {{cache:TargetTableToRestoreName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestoreFromPointInTimeAssumeRole}} |
    Then SSM automation document "Digito-RestoreToPointInTime_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And drop Dynamo DB table with the name {{cache:TargetTableToRestoreName}} and wait for 300 seconds with interval 20 seconds

  # TODO In this Scenario it would be good to test how many Alarms has been changed (the output of SwitchAlarmsToTargetTable)
  # need to improve current code functionality of the tests by adding appropriate step
  # this will be done in a "Full Cucumber test" task
  Scenario: Restores table to the latest available point. Change Alarms
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                | ResourceType |
      | resource_manager/cloud_formation_templates/DynamoDBTemplateWithAutoScaling.yml | ON_DEMAND    |
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                       | ResourceType |
      | documents/dynamodb/sop/restore_to_point_in_time/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestoreToPointInTime_2020-04-01" SSM document
    And the cached input parameters
      | TargetTableToRestoreName |
      | TargetTableToRestore     |
    And drop Dynamo DB table with the name {{cache:TargetTableToRestoreName}} and wait for 300 seconds with interval 20 seconds
    When SSM automation document "Digito-RestoreToPointInTime_2020-04-01" executed
      | DynamoDBTableSourceName                                      | DynamoDBTableTargetName            | AutomationAssumeRole                                                               | DynamoDBSourceTableAlarmNames |
      | {{cfn-output:DynamoDBTemplateWithAutoScaling>DynamoDBTable}} | {{cache:TargetTableToRestoreName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestoreFromPointInTimeAssumeRole}} | WriteThrottleEvents           |
    Then SSM automation document "Digito-RestoreToPointInTime_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And drop Dynamo DB table with the name {{cache:TargetTableToRestoreName}} and wait for 300 seconds with interval 20 seconds

  Scenario: Restores table to the latest available point. With Indexes
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                       | ResourceType |
      | resource_manager/cloud_formation_templates/DynamoDBTemplateWithIndex.yml                              | ON_DEMAND    |
      | documents/dynamodb/sop/restore_to_point_in_time/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestoreToPointInTime_2020-04-01" SSM document
    And the cached input parameters
      | TargetTableToRestoreName |
      | TargetTableToRestore     |
    And drop Dynamo DB table with the name {{cache:TargetTableToRestoreName}} and wait for 300 seconds with interval 20 seconds
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
    And the cached input parameters
      | TargetTableToRestoreName |
      | TargetTableToRestore     |
    And drop Dynamo DB table with the name {{cache:TargetTableToRestoreName}} and wait for 300 seconds with interval 20 seconds
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
    And the cached input parameters
      | TargetTableToRestoreName |
      | TargetTableToRestore     |
    And drop Dynamo DB table with the name {{cache:TargetTableToRestoreName}} and wait for 300 seconds with interval 20 seconds
    When SSM automation document "Digito-RestoreToPointInTime_2020-04-01" executed
      | DynamoDBTableSourceName                                 | DynamoDBTableTargetName            | AutomationAssumeRole                                                               |
      | {{cfn-output:DynamoDBTemplateWithStream>DynamoDBTable}} | {{cache:TargetTableToRestoreName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestoreFromPointInTimeAssumeRole}} |
    Then SSM automation document "Digito-RestoreToPointInTime_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And Wait for the SSM automation document "Digito-RestoreToPointInTime_2020-04-01" execution is on step "UpdateTargetDynamoDBTableStream" in status "Success" for "600" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And drop Dynamo DB table with the name {{cache:TargetTableToRestoreName}} and wait for 300 seconds with interval 20 seconds


  Scenario: Restores table to the latest available point with enabled kinesis streaming destination
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                       | ResourceType |
      | resource_manager/cloud_formation_templates/DynamoDBTemplate.yml                                       | ON_DEMAND    |
      | documents/dynamodb/sop/restore_to_point_in_time/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestoreToPointInTime_2020-04-01" SSM document
    And enable kinesis stream {{cfn-output:DynamoDBTemplate>KinesisStreamArn}} on dynamodb table {{cfn-output:DynamoDBTemplate>DynamoDBTable}}
    And the cached input parameters
      | TargetTableToRestoreName |
      | TargetTableToRestore     |
    And drop Dynamo DB table with the name {{cache:TargetTableToRestoreName}} and wait for 300 seconds with interval 20 seconds
    When SSM automation document "Digito-RestoreToPointInTime_2020-04-01" executed
      | DynamoDBTableSourceName                       | DynamoDBTableTargetName            | AutomationAssumeRole                                                               |
      | {{cfn-output:DynamoDBTemplate>DynamoDBTable}} | {{cache:TargetTableToRestoreName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestoreFromPointInTimeAssumeRole}} |
    And Wait for the SSM automation document "Digito-RestoreToPointInTime_2020-04-01" execution is on step "AddTargetDynamoDBTableKinesisDestination" in status "Success" for "600" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    Then SSM automation document "Digito-RestoreToPointInTime_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And drop Dynamo DB table with the name {{cache:TargetTableToRestoreName}} and wait for 300 seconds with interval 20 seconds


  Scenario: Restores table to the latest available point with TTL enabled
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                       | ResourceType |
      | resource_manager/cloud_formation_templates/DynamoDBTemplate.yml                                       | ON_DEMAND    |
      | documents/dynamodb/sop/restore_to_point_in_time/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestoreToPointInTime_2020-04-01" SSM document
    And the cached input parameters
      | TargetTableToRestoreName |
      | TargetTableToRestore     |
    And the cached input parameters
      | TtlAttributeName |
      | end_date         |
    And enable ttl on dynamodb table {{cfn-output:DynamoDBTemplate>DynamoDBTable}} with attribute name {{cache:TtlAttributeName}}
    And drop Dynamo DB table with the name {{cache:TargetTableToRestoreName}} and wait for 300 seconds with interval 20 seconds
    When SSM automation document "Digito-RestoreToPointInTime_2020-04-01" executed
      | DynamoDBTableSourceName                       | DynamoDBTableTargetName            | AutomationAssumeRole                                                               |
      | {{cfn-output:DynamoDBTemplate>DynamoDBTable}} | {{cache:TargetTableToRestoreName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestoreFromPointInTimeAssumeRole}} |
    And Wait for the SSM automation document "Digito-RestoreToPointInTime_2020-04-01" execution is on step "AddTargetDynamoDBTableKinesisDestination" in status "Success" for "600" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    Then SSM automation document "Digito-RestoreToPointInTime_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And drop Dynamo DB table with the name {{cache:TargetTableToRestoreName}} and wait for 300 seconds with interval 20 seconds


