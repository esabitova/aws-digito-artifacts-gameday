@docdb
Feature: SSM automation document to recover the database into a known good state.

  Scenario: Recover the database into a known good state using latest point-in-time
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                      | ResourceType |
      | resource_manager/cloud_formation_templates/DocDbTemplate.yml                                         | ON_DEMAND    |
      | documents/docdb/sop/restore_from_point_in_time/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestoreFromPointInTime_2020-09-21" SSM document
    And cache current number of instances as "NumberOfInstances" "before" SSM automation execution
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    And cache cluster params includingAZ="False" in object "ClusterInfo" in step "before"
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
    And delete replaced cluster instances and wait for their removal for "600" seconds
      | ReplacedDBClusterIdentifier                      |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    And delete replaced cluster and wait for cluster deletion for "600" seconds
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    And sleep for "60" seconds


  Scenario: Recover the database into a known good state using earliest point-in-time
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                      | ResourceType |
      | resource_manager/cloud_formation_templates/DocDbTemplate.yml                                         | ON_DEMAND    |
      | documents/docdb/sop/restore_from_point_in_time/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
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
    And delete replaced cluster instances and wait for their removal for "600" seconds
      | ReplacedDBClusterIdentifier                      |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    And delete replaced cluster and wait for cluster deletion for "600" seconds
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    And sleep for "60" seconds
