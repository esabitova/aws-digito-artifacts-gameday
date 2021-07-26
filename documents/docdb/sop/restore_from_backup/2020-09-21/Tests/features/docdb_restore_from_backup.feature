@docdb
Feature: SSM automation document to recover the database into a known good state.

  Scenario: Recover the database into a known good state using latest snapshot
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                               | ResourceType |
      | resource_manager/cloud_formation_templates/DocDbTemplate.yml                                  | ON_DEMAND    |
      | documents/docdb/sop/restore_from_backup/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-DocDbRestoreFromBackup_2020-09-21" SSM document
    And cache cluster params includingAZ="True" in object "ClusterParams" in step "before"
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    And cache current number of instances as "NumberOfInstances" "before" SSM automation execution
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    And wait for cluster snapshot creation for "600" seconds
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    When SSM automation document "Digito-DocDbRestoreFromBackup_2020-09-21" executed
      | DBClusterIdentifier                              | AutomationAssumeRole                                                               |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoDocDbRestoreFromBackupAssumeRole}} |
    Then SSM automation document "Digito-DocDbRestoreFromBackup_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And wait for instances to be available for "120" seconds
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    And cache cluster params includingAZ="True" in object "ClusterParams" in step "after"
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    And cache current number of instances as "ActualNumberOfInstances" "after" SSM automation execution
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    Then assert "ActualNumberOfInstances" at "after" became equal to "NumberOfInstances" at "before"
    And assert "ClusterParams" at "before" became equal to "ClusterParams" at "after"
    And delete replaced cluster instances and wait for their removal for "600" seconds
      | ReplacedDBClusterIdentifier                      |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    And delete replaced cluster and wait for cluster deletion for "600" seconds
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    And delete cluster snapshot

  Scenario: Recover the database into a known good state using specified snapshot identifier
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                               | ResourceType |
      | resource_manager/cloud_formation_templates/DocDbTemplate.yml                                  | ON_DEMAND    |
      | documents/docdb/sop/restore_from_backup/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-DocDbRestoreFromBackup_2020-09-21" SSM document
    And cache cluster params includingAZ="True" in object "ClusterParams" in step "before"
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    And cache current number of instances as "NumberOfInstances" "before" SSM automation execution
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    And wait for cluster snapshot creation for "600" seconds
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    When SSM automation document "Digito-DocDbRestoreFromBackup_2020-09-21" executed
      | DBSnapshotIdentifier        | DBClusterIdentifier                              | AutomationAssumeRole                                                               |
      | {{cache:before>SnapshotId}} | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoDocDbRestoreFromBackupAssumeRole}} |
    Then SSM automation document "Digito-DocDbRestoreFromBackup_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And wait for instances to be available for "120" seconds
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    And cache cluster params includingAZ="True" in object "ClusterParams" in step "after"
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    And cache current number of instances as "ActualNumberOfInstances" "after" SSM automation execution
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    Then assert "ActualNumberOfInstances" at "after" became equal to "NumberOfInstances" at "before"
    And assert "ClusterParams" at "before" became equal to "ClusterParams" at "after"
    And delete replaced cluster instances and wait for their removal for "600" seconds
      | ReplacedDBClusterIdentifier                      |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    And delete replaced cluster and wait for cluster deletion for "600" seconds
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    And delete cluster snapshot
