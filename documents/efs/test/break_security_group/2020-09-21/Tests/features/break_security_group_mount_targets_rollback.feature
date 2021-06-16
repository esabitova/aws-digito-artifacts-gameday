@efs
Feature: SSM automation document to test EFS behavior after breaking security group id

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document to test EFS behavior after breaking security group id
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                     | ResourceType |
      | resource_manager/cloud_formation_templates/EFSTemplate.yml                                          | ON_DEMAND    |
      | documents/efs/test/break_security_group/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml       | ASSUME_ROLE  |
    And published "Digito-EFSBreakSecurityGroup_2020-09-21" SSM document
    And cache security group id for a mount target as "SecurityGroupId" "before" SSM automation execution
      | MountTargetId                            |
      | {{cfn-output:EFSTemplate>EFSMountTarget}}|
    When SSM automation document "Digito-EFSBreakSecurityGroup_2020-09-21" executed
      | FileSystemId                     | ClientConnectionsAlarmName                            | MountTargetIds                            | AutomationAssumeRole                                                              |
      | {{cfn-output:EFSTemplate>EFSID}} | {{cfn-output:EFSTemplate>ClientConnectionsAlarmName}} | {{cfn-output:EFSTemplate>EFSMountTarget}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoEFSBreakSecurityGroupAssumeRole}} |
    Then Wait for the SSM automation document "Digito-EFSBreakSecurityGroup_2020-09-21" execution is on step "AssertAlarmToBeRed" in status "InProgress"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And terminate "Digito-EFSBreakSecurityGroup_2020-09-21" SSM automation document
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    Then Wait for the SSM automation document "Digito-EFSBreakSecurityGroup_2020-09-21" execution is on step "TriggerRollback" in status "Success"
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|

    Then SSM automation document "Digito-EFSBreakSecurityGroup_2020-09-21" execution in status "Cancelled"
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|

    Then cache rollback execution id
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|
    # Rollback verification
    Then SSM automation document "Digito-EFSBreakSecurityGroup_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>2}} |
    And cache security group id for a mount target as "SecurityGroupId" "after" SSM automation execution
      | MountTargetId                            |
      | {{cfn-output:EFSTemplate>EFSMountTarget}}|
    And assert "SecurityGroupId" at "before" became equal to "SecurityGroupId" at "after"