@docdb
Feature: SSM automation document to recover the database into a known good state.

  Scenario: Recover the database into a known good state using latest point-in-time
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                       | ResourceType | VPC                      | VPCCIDR                    | PrivateSubnet01                                | PrivateSubnet02                                | KmsKey                              |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                                             | SHARED       |                          |                            |                                                |                                                |                                     |
      | resource_manager/cloud_formation_templates/shared/KMS.yml                                             | SHARED       |                          |                            |                                                |                                                |                                     |
      | resource_manager/cloud_formation_templates/DocDbTemplate.yml                                          | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>VPCCidr}} | {{cfn-output:VPC>PrivateSubnetWithInternet01}} | {{cfn-output:VPC>PrivateSubnetWithInternet02}} | {{cfn-output:KMS>EncryptAtRestKey}} |
      | documents/docdb/sop/restore_from_point_in_time/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml  | ASSUME_ROLE  |                          |                            |                                                |                                                |                                     |
    And published "Digito-RestoreFromPointInTime_2020-09-21" SSM document
    And cache current number of instances as "NumberOfInstances" "before" SSM automation execution
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    And cache cluster params includingAZ="False" in object "ClusterInfo" in step "before"
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    And prepare replaced cluster for teardown
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    When SSM automation document "Digito-RestoreFromPointInTime_2020-09-21" executed
      | DBClusterIdentifier                              | AutomationAssumeRole                                                               |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestoreFromPointInTimeAssumeRole}} |
    Then SSM automation document "Digito-RestoreFromPointInTime_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And wait for instances to be available for "120" seconds
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    And cache current number of instances as "ActualNumberOfInstances" "after" SSM automation execution
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    And cache cluster params includingAZ="False" in object "ClusterInfo" in step "after"
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    And assert "ActualNumberOfInstances" at "after" became equal to "NumberOfInstances" at "before"
    And assert "ClusterInfo" at "after" became equal to "ClusterInfo" at "before"


  Scenario: Recover the database into a known good state using earliest point-in-time
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                       | ResourceType | VPC                      | VPCCIDR                    | PrivateSubnet01                                | PrivateSubnet02                                | KmsKey                              |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                                             | SHARED       |                          |                            |                                                |                                                |                                     |
      | resource_manager/cloud_formation_templates/shared/KMS.yml                                             | SHARED       |                          |                            |                                                |                                                |                                     |
      | resource_manager/cloud_formation_templates/DocDbTemplate.yml                                          | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>VPCCidr}} | {{cfn-output:VPC>PrivateSubnetWithInternet01}} | {{cfn-output:VPC>PrivateSubnetWithInternet02}} | {{cfn-output:KMS>EncryptAtRestKey}} |
      | documents/docdb/sop/restore_from_point_in_time/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml  | ASSUME_ROLE  |                          |                            |                                                |                                                |                                     |
    And published "Digito-RestoreFromPointInTime_2020-09-21" SSM document
    And cache current number of instances as "NumberOfInstances" "before" SSM automation execution
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    And cache cluster params includingAZ="False" in object "ClusterInfo" in step "before"
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    And cache earliest restorable time as "EarliestRestorableTime" in "before" step
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    And prepare replaced cluster for teardown
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    When SSM automation document "Digito-RestoreFromPointInTime_2020-09-21" executed
      | DBClusterIdentifier                              | RestoreToDate                           | AutomationAssumeRole                                                               |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} | {{cache:before>EarliestRestorableTime}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestoreFromPointInTimeAssumeRole}} |
    Then SSM automation document "Digito-RestoreFromPointInTime_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And wait for instances to be available for "120" seconds
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    And cache current number of instances as "ActualNumberOfInstances" "after" SSM automation execution
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    And cache cluster params includingAZ="False" in object "ClusterInfo" in step "after"
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    And assert "ActualNumberOfInstances" at "after" became equal to "NumberOfInstances" at "before"
    And assert "ClusterInfo" at "after" became equal to "ClusterInfo" at "before"