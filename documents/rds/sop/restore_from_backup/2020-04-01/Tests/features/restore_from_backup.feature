@rds @restore_from_backup @integration
Feature: SSM automation document for restore from backup.
  Exercise SSM automation document for restore from backup.

  Scenario: Restore RDS instance from backup WetRun.
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                             | ResourceType | DBInstanceClass | AllocatedStorage |
      | resource_manager/cloud_formation_templates/RdsCfnTemplateSingleMAZ.yml                      | ON_DEMAND    | db.t3.small     | 20               |
      | documents/rds/sop/restore_from_backup/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                 |                  |
    And published "Digito-RdsRestoreFromBackup_2020-04-01" SSM document

    When SSM automation document "Digito-RdsRestoreFromBackup_2020-04-01" executed
      | DbInstanceIdentifier                              | AutomationAssumeRole                                                             | Dryrun |
      | {{cfn-output:RdsCfnTemplateSingleMAZ>InstanceId}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRdsRestoreFromBackupAssumeRole}} | false  |

    Then Wait for the SSM automation document "Digito-RdsRestoreFromBackup_2020-04-01" execution is on step "TrafficRedirectionPause" in status "Waiting"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And SSM Automation Resume for execution "{{cache:SsmExecutionId>1}}" on step "TrafficRedirectionPause"


    And SSM automation document "Digito-RdsRestoreFromBackup_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    And cache ssm step execution interval
      | ExecutionId                | StepName        |
      | {{cache:SsmExecutionId>1}} | RecordStartTime |

    And assert db instance {{cfn-output:RdsCfnTemplateSingleMAZ>InstanceId}} creation date is after {{cache:SsmStepExecutionInterval>1>RecordStartTime>StartTime}}


  Scenario: Restore RDS instance from backup DryRun.
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                             | ResourceType | DBInstanceClass | AllocatedStorage |
      | resource_manager/cloud_formation_templates/RdsCfnTemplateSingleMAZ.yml                      | ON_DEMAND    | db.t3.small     | 20               |
      | documents/rds/sop/restore_from_backup/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                 |                  |
    And published "Digito-RdsRestoreFromBackup_2020-04-01" SSM document

    When SSM automation document "Digito-RdsRestoreFromBackup_2020-04-01" executed
      | DbInstanceIdentifier                              | AutomationAssumeRole                                                             | Dryrun |
      | {{cfn-output:RdsCfnTemplateSingleMAZ>InstanceId}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRdsRestoreFromBackupAssumeRole}} | true  |

    Then SSM automation document "Digito-RdsRestoreFromBackup_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    And cache ssm step execution interval
      | ExecutionId                | StepName        |
      | {{cache:SsmExecutionId>1}} | RecordStartTime |

    And assert db instance {{cfn-output:RdsCfnTemplateSingleMAZ>InstanceId}} creation date is after {{cache:SsmStepExecutionInterval>1>RecordStartTime>StartTime}}
