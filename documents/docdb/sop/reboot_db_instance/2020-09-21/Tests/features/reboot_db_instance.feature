@docdb
Feature: SSM automation document to recover the database into a known good state.

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document to reboot DB instance when the database doesn’t respond to any requests
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                              | ResourceType |
      | resource_manager/cloud_formation_templates/DocDbTemplate.yml                                 | ON_DEMAND    |
      | documents/docdb/sop/reboot_db_instance/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RebootDbInstance_2020-09-21" SSM document
    When SSM automation document "Digito-RebootDbInstance_2020-09-21" executed
      | DBClusterIdentifier                              | DBInstanceIdentifier                                      | AutomationAssumeRole                                                         |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} | {{cfn-output:DocDbTemplate>DBInstanceReplicaIdentifier}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRebootDbInstanceAssumeRole}} |

    Then SSM automation document "Digito-RebootDbInstance_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
