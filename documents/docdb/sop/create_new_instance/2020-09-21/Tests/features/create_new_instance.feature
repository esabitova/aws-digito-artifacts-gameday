@docdb
Feature: SSM automation document to recover the database into a known good state.

  Scenario: Create a new instance in a specified AZ/Region
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                               | ResourceType |
      | resource_manager/cloud_formation_templates/DocDbTemplate.yml                                  | ON_DEMAND    |
      | documents/docdb/sop/create_new_instance/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-CreateNewDocDbInstance_2020-09-21" SSM document
    And the cached input parameters
      | AvailabilityZone | DBInstanceIdentifier |
      | us-east-1c       | new-docdb-instance1  |
    And cache current number of clusters as "NumberOfInstances" "before" SSM automation execution
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    And cache property "ExpectedAvailabilityZone" in step "before" SSM automation execution
      | Value                      |
      | {{cache:AvailabilityZone}} |
    When SSM automation document "Digito-CreateNewDocDbInstance_2020-09-21" executed
      | DBClusterIdentifier                              | DBInstanceIdentifier           | AvailabilityZone           | AutomationAssumeRole                                                          |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} | {{cache:DBInstanceIdentifier}} | {{cache:AvailabilityZone}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoCreateNewInstanceAssumeRole}} |
    Then SSM automation document "Digito-CreateNewDocDbInstance_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache current number of clusters as "ActualNumberOfInstances" "after" SSM automation execution
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    Then sleep for "60" seconds
    And cache az in property "ActualAvailabilityZone" in step "after" SSM automation execution
      | DBInstanceIdentifier           |
      | {{cache:DBInstanceIdentifier}} |
    Then assert "NumberOfInstances" at "before" became not equal to "ActualNumberOfInstances" at "after"
    Then assert "ExpectedAvailabilityZone" at "before" became equal to "ActualAvailabilityZone" at "after"


  Scenario: Create a new instance without specifying AZ
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                               | ResourceType |
      | resource_manager/cloud_formation_templates/DocDbTemplate.yml                                  | ON_DEMAND    |
      | documents/docdb/sop/create_new_instance/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-CreateNewDocDbInstance_2020-09-21" SSM document
    And the cached input parameters
      | DBInstanceIdentifier |
      | new-docdb-instance2  |
    And cache current number of clusters as "NumberOfInstances" "before" SSM automation execution
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    When SSM automation document "Digito-CreateNewDocDbInstance_2020-09-21" executed
      | DBClusterIdentifier                              | DBInstanceIdentifier           | AutomationAssumeRole                                                          |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} | {{cache:DBInstanceIdentifier}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoCreateNewInstanceAssumeRole}} |
    Then SSM automation document "Digito-CreateNewDocDbInstance_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache current number of clusters as "ActualNumberOfInstances" "after" SSM automation execution
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    Then sleep for "60" seconds
    And cache az in property "ActualAvailabilityZone" in step "after" SSM automation execution
      | DBInstanceIdentifier           |
      | {{cache:DBInstanceIdentifier}} |
    Then assert "NumberOfInstances" at "before" became not equal to "ActualNumberOfInstances" at "after"
    Then assert instance AZ value "ActualAvailabilityZone" at "after" is one of cluster AZs
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |