@ebs @integration @ebs_increase_volume
Feature: SSM automation document Digito-EBSRestoreFromBackup_2020-05-26

  Scenario: Execute SSM automation document Digito-EBSIncreaseVolumeSize_2020-05-26
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                       | ResourceType |InstanceType |
      | resource_manager/cloud_formation_templates/Ec2WithEbsCfnTemplate.yml  | ON_DEMAND    |t2.small     |

    And the cloud formation templates as integration test resources
      | CfnTemplatePath                                                       | ResourceType |
      | documents/ebs/sop/increase_volume_size/2020-05-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |

    And published "Digito-EBSIncreaseVolumeSize_2020-05-26" SSM document

    When SSM automation document "Digito-EBSIncreaseVolumeSize_2020-05-26" executed
      | InstanceIdentifier                              | AutomationAssumeRole                                                              | SizeGib | Partition | DeviceName |
      | {{cfn-output:Ec2WithEbsCfnTemplate>InstanceId}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoEbsIncreaseVolumeSizeAssumeRole}} | 9       | 1         | /dev/xvda  |

    Then SSM automation document "Digito-EBSRestoreFromBackup_2020-05-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
