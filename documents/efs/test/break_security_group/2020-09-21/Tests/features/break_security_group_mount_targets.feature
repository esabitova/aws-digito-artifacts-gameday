@efs
Feature: SSM automation document to test EFS behavior after breaking security group id

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document to test EFS behavior after breaking security group id
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                     | ResourceType |
      | resource_manager/cloud_formation_templates/EFSTemplate.yml                                          | ON_DEMAND    |
      | documents/efs/test/break_security_group/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml       | ASSUME_ROLE  |
    And published "Digito-BreakEFSSecurityGroupTest_2020-09-21" SSM document
    And cache security group id for a mount target as "SecurityGroupId" "before" SSM automation execution
      | MountTargetId                            |
      | {{cfn-output:EFSTemplate>EFSMountTarget}}|
    And SSM automation document "Digito-BreakEFSSecurityGroupTest_2020-09-21" executed
      | FileSystemId                     | ClientConnectionsAlarmName                            | MountTargetIds                            | AutomationAssumeRole                                                                  |
      | {{cfn-output:EFSTemplate>EFSID}} | {{cfn-output:EFSTemplate>ClientConnectionsAlarmName}} | {{cfn-output:EFSTemplate>EFSMountTarget}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoBreakEFSSecurityGroupTestAssumeRole}} |

    When SSM automation document "Digito-BreakEFSSecurityGroupTest_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    Then cache security group id for a mount target as "SecurityGroupId" "after" SSM automation execution
      | MountTargetId                            |
      | {{cfn-output:EFSTemplate>EFSMountTarget}}|
    And assert "SecurityGroupId" at "before" became equal to "SecurityGroupId" at "after"

