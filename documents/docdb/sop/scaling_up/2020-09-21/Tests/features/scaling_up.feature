@docdb
Feature: SSM automation document for scaling up DocDb instances.

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document for scaling up DocumentDb instances
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                      | ResourceType |
      | resource_manager/cloud_formation_templates/DocDbTemplate.yml                         | ON_DEMAND    |
      | documents/docdb/sop/scaling_up/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-CreateNewDocDbInstance_2020-09-21" SSM document
    When SSM automation document "Digito-ScalingUp_2020-09-21" executed
      | DBClusterIdentifier                                   | DBInstanceReplicaIdentifier | AutomationAssumeRole                                                  |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}}      | new-docdb-replica                | {{cfn-output:AutomationAssumeRoleTemplate>DigitoScalingUpAssumeRole}} |

    Then SSM automation document "Digito-ScalingUp_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |