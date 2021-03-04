@docdb
Feature: SSM automation document to recover the database into a known good state.

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document to create a new instance in a specified AZ/Region
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                              | ResourceType |
      | resource_manager/cloud_formation_templates/DocDbTemplate.yml                                 | ON_DEMAND    |
      | documents/docdb/sop/create_new_instance/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-CreateNewInstance_2020-09-21" SSM document
    When SSM automation document "Digito-CreateNewInstance_2020-09-21" executed
      | DBClusterIdentifier                              | DBInstanceIdentifier | AvailabilityZone | AutomationAssumeRole                                                         |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} | new-docdb-instance   | eu-west-1c      | {{cfn-output:AutomationAssumeRoleTemplate>DigitoCreateNewInstanceAssumeRole}} |

    Then SSM automation document "Digito-CreateNewInstance_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |