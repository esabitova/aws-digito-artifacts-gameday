@ebs @integration @ebs_restore_backup
Feature: SSM automation document Digito-EBSRestoreFromBackup_2020-05-26

  Scenario: Execute SSM automation document Digito-EBSRestoreFromBackup_2020-05-26
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                       | ResourceType |InstanceType |
      | resource_manager/cloud_formation_templates/Ec2WithEbsCfnTemplate.yml  | ON_DEMAND    |t2.small     |

    And the cloud formation templates as integration test resources
      | CfnTemplatePath                                                       | ResourceType |
      | documents/ebs/sop/restore_from_backup/2020-05-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |

    And Create snapshot as "snapshot" property "SnapshotId"
      | VolumeId                             |
      | {{cfn-output:Ec2WithEbsCfnTemplate>VolumeId}} |

    And published "Digito-EBSRestoreFromBackup_2020-05-26" SSM document

    When SSM automation document "Digito-EBSRestoreFromBackup_2020-05-26" executed
      | EBSSnapshotIdentifier         | AutomationAssumeRole                                                             | TargetAvailabilityZone |
      | {{cache:snapshot>SnapshotId}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoEbsRestoreFromBackupAssumeRole}} | us-east-2a             |

    Then SSM automation document "Digito-EBSRestoreFromBackup_2020-05-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
